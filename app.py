import os
import re
import datetime

from config import Config
from database import db, Posts, Users, Authors, Titles, Favorites
from flask import Flask, redirect, render_template, request, session
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from geopy.geocoders import Nominatim
from helpers import add_bold_tags, allowed_files, login_required, post_details_dict
from PIL import Image
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash


# Configure application.
app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
Session(app)
geolocator = Nominatim(user_agent="picturesque")
admin = Admin(app)

# Add ModelViews to display tables in "/admin" route.
admin.add_view(ModelView(Users, db.session))
admin.add_view(ModelView(Posts, db.session))
admin.add_view(ModelView(Authors, db.session))
admin.add_view(ModelView(Titles, db.session))
admin.add_view(ModelView(Favorites, db.session))

# Ensure responses aren't cached.


@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Open homepage
@ app.route("/")
def index():
    try:
        user = Users.query.filter_by(_id=session["user_id"]).first()
    except KeyError:
        user = None
    return render_template("index.html", user=user)


# Log in.
@ app.route("/login", methods=["GET", "POST"])
def login():
    # Forget any user id.
    session.clear()

    # Prepare variables ready to be send back to 'login.html' in case of invalid input.
    invalid = False
    name = ''

    # Log in user.
    if request.method == "POST":
        if not request.form.get("username") or not request.form.get("password"):
            invalid = True
        name = request.form.get("username")
        password = request.form.get("password")

        # Get the previous url and pass it as the next one.
        next_url = request.form.get("next")
        # If no previouse url given, redirect to the home page.
        next_url = next_url or "/"

        # Check password.
        user = Users.query.filter_by(username=name).first()
        try:
            if check_password_hash(user.hash, password):
                session["user_id"] = user._id
                return redirect(next_url)
            else:
                invalid = True
        except AttributeError:
            invalid = True

    return render_template("login.html", invalid=invalid, name=name)


# Log out.
@ app.route("/logout")
@ login_required
def logout():
    # Forget any user_id.
    session.clear()

    return redirect("/")


# Register.
@ app.route("/register", methods=["GET", "POST"])
def register():
    # Forget any logged user.
    session.clear()

    # Prepare variables ready to be send back to 'login.html' in case of invalid input.
    invalid = False
    problem = None
    name = ""

    # Register new user.
    if request.method == "POST":
        # Check if all of the entries are correct.
        if not request.form.get("username") or \
                not request.form.get("password") or \
            not request.form.get("confirmation") or \
                len(request.form.get("password")) < 8 or\
                not re.findall('\d', request.form.get("password")) or \
                not re.findall('[a-zA-Z]', request.form.get("password")) or \
                not request.form.get("password") == request.form.get("confirmation"):
            invalid = True
            problem = "other"

        # Check if the name is available.
        elif Users.query.filter_by(username=request.form.get("username")).first():
            invalid = True
            problem = "wrong_name"
            name = request.form.get("username")

        # Save new user's details.
        else:
            name = request.form.get("username")
            hash = generate_password_hash(request.form.get(
                "password"), method='pbkdf2:sha256', salt_length=8)
            new = Users(username=name, hash=hash)
            db.session.add(new)
            db.session.commit()

            # Remember which user is logged in.
            session["user_id"] = new._id

            # Get the previous url and pass it as the next one.
            next_url = request.form.get("next")
            # If no previouse url given, redirect to the home page.
            next_url = next_url or "/"
            return redirect(next_url)

    return render_template("register.html", invalid=invalid, problem=problem, name=name)


# Open the new post post.
@ app.route("/new_entry", methods=["GET"])
@ login_required
def new_entry(invalid={'invalid': False}):
    # Prepare list of authors and titles for `datalist`.
    authors = list(a[0] for a in db.session.query(Authors.name).all())
    titles = list(t[0]
                  for t in db.session.query(Titles.title).distinct().all())
    return render_template("new_entry.html", invalid=invalid, authors=authors, titles=titles)


# Function that verifies and saves both new post and modified one.
@ app.route("/uploader", methods=["GET", "POST"])
@ login_required
def upload_file():
    if request.method == "POST":
        # Create a dictionary to pass it to the client in case of invalid input.
        new_author = request.form.get("author")
        new_title = request.form.get("title")
        new_quote = request.form.get("quote")
        new_place = request.form.get("place")
        invalid = {
            'invalid': False,
            'author': new_author,
            'title': new_title,
            'quote': new_quote,
            'place': new_place,
        }

        # If modify_id exists, the whole function is in MODIFY mode.
        modify_id = session.get('modify', None)

        # If location is given, it means that the user have just placed the marker
        # and the rest of the details have just been saved.
        if request.form.get("location"):
            location = request.form.get("location")
            loc = location.strip('()')
            latitude, longitude = tuple(s.strip() for s in loc.split(','))
            id = session.get("modify", None) or session["post_id"]

            # Save location.
            entry = db.session.query(Posts).get(id)
            entry.latitude = latitude
            entry.longitude = longitude

            # Save the name of the place.
            place = geolocator.geocode(loc)
            entry.place = place.address
            db.session.commit()
            session.pop("post_id", None)
            session.pop("modify", None)
            return redirect(f"/post/?p={id}")

        # Clear session["post_id"].
        session.pop("post_id", None)

        # Check if all expected fields were completed, otherwise load the page again.
        # If in MODIFY mode, ignore empty fields.
        file = request.files["file"]
        if not modify_id and not (new_author and new_title and new_quote and file):
            invalid["invalid"] = True
            return new_entry(invalid)

        # If in MODIFY mode, change place.
        if modify_id:
            current_post = db.session.query(Posts).get(modify_id)
            # Do nothing, if nothing in the place field has changed.
            if not (current_post.place or new_place) or \
                    current_post.place == new_place:
                new_place = None
            # Delete place, if the user has deleted the place's name.
            elif current_post.place and not new_place:
                current_post.place = current_post.latitude = current_post.longitude = None

        # Check if geocode can find the location (if given).
        if new_place:
            location = geolocator.geocode(new_place)
            if not location:
                invalid['invalid'] = True
                invalid['invalid_place'] = True
                return new_entry(invalid)

        # Check if author is in the database.
        if new_author:
            author = Authors.query.filter_by(name=new_author).first()
            if author:
                # Get the author's id.
                new_author_id = author._id
            else:
                # Create new author.
                new_author = Authors(name=new_author)
                db.session.add(new_author)
                db.session.flush()
                new_author_id = new_author._id
        else:
            new_author_id = current_post.author._id

        # Check if title (associated with the same author) is in the database.
        if new_title:
            title = Titles.query.filter_by(title=new_title).first()
            if title and title.author_id == new_author_id:
                # Get the title's id.
                new_title_id = title._id
            else:
                # Create new title.
                new_title = Titles(title=new_title, author_id=new_author_id)
                db.session.add(new_title)
                db.session.flush()
                new_title_id = new_title._id
        else:
            new_title_id = current_post.title._id

        # Create new filename based on the time of creation.

        # If in MODIFY mode, keep the old filename.
        if modify_id:
            item = current_post.item.split('.')[0]
        else:
            item = None
            # What's the time?
            added_time = datetime.datetime.utcnow()
            time_string = added_time.strftime('%y%m%d%H%M%S')

        # Get user's id.
        user_id = session["user_id"]

        if file:
            filename = file.filename

            # Check if file's extension is allowed.
            if filename == '' or not allowed_files(filename):
                invalid["invalid"] = True

            # Extract the photo's extension.
            ext = filename.rsplit('.', 1)[1].lower()

            # Create prefix for photo, thumbnails and quotes names, and check if it is unique.
            if not item:
                item = f"{str(user_id)}_{time_string}"
                while item + '.' + ext in {x.item for x in Posts.query.all()}:
                    # Prefix should have structure: 'xx_xxxxxxxxxxxx' (where xs are digits) if it's unique.
                    # If it is not unique, add new segment.
                    # If it already looks like: 'xx_xxxxxxxxxxxx_xx', increment the last segment.
                    segments = item.split('_')
                    number_of_segments = len(segments)
                    if number_of_segments > 2:
                        segments[-1] = str(int(segments[-1]) + 1)
                    else:
                        segments.append('1')
                    item = '_'.join(segments)

            # Save photo.
            filename = item + '.' + ext
            path = os.path.join(
                app.config["UPLOAD_FOLDER"], 'photos', filename)
            # If in MODIFY mode, delete the old photo first.
            if modify_id:
                old_path = os.path.join(
                    app.config["UPLOAD_FOLDER"], 'photos', current_post.item)
                if os.path.exists(old_path):
                    os.remove(old_path)

            with Image.open(file) as img:
                img.save(path, quality=50)

            # Create and save thumbnail.
            with Image.open(file) as img:
                img.thumbnail(app.config["THUMBNAIL_SIZE"])
                thumb_name = "thumb_" + filename
                path = os.path.join(
                    app.config["UPLOAD_FOLDER"], 'thumbnails', thumb_name)
                # If in MODIFY mode, delete the old thumbnail first.
                if modify_id:
                    old_path = os.path.join(
                        app.config["UPLOAD_FOLDER"], 'thumbnails', "thumb_" + current_post.item)
                    if os.path.exists(old_path):
                        os.remove(old_path)
                img.save(path)
            file.close()

        else:
            ext = current_post.item.split('.')[-1]

        # Save quote.
        if not (modify_id and new_quote == ''):
            quote_name = "quote_" + item + '.txt'
            path = os.path.join(
                app.config["UPLOAD_FOLDER"], 'quotes', quote_name)
            with open(path, 'w', encoding='utf-8', newline='') as file:
                file.write(new_quote)

        item += '.' + ext

        # Save the new post or the changed one in the database.
        if modify_id:
            current_post.author_id = new_author_id
            current_post.title_id = new_title_id
            current_post.item = item
            post_id = current_post._id
        else:
            new = Posts(user_id=user_id, author_id=new_author_id, title_id=new_title_id,
                        item=item, added=added_time)
            db.session.add(new)
            db.session.flush()
            session["post_id"] = post_id = new._id

        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            invalid["invalid"] = True
            return new_entry(invalid)

    # Prepare to open "post.html" where the user will be able to place marker.
    if new_place:
        # Find coordinates of the entered place.
        latitude = location.latitude
        longitude = location.longitude

        # Create post details dictionary and add new coordinates.
        post = post_details_dict(post_id)
        post['latitude'] = location.latitude
        post['longitude'] = location.longitude

        logged_user = {"user_id": user_id}
        return render_template("post.html", post=post, coordinates=None, logged_user=logged_user)
    else:
        # Remove 'modify' key from the session.
        session.pop("modify", None)

    # Display new post.
    return display_post(post_id)


# Prepare details of the post to be modified.
@app.route("/modify", methods=["GET", "POST"])
@login_required
def modify():
    # Get post id.
    post_id = request.form.get("post_id")

    # Make dictionary for the "new_entry.html".
    post = post_details_dict(post_id, scope=(
        'author', 'title', 'photo', 'quote', 'place'))
    invalid = dict(
        invalid="modify",
        author=post["author"],
        title=post["title"],
        quote=post["quote"].replace('\n', '\\n'),
        photo=post["photo"],
        place=post["place"],
        id=post["id"],
    )

    # Add 'modify' key to the session, to indicate that the post passed to new_entry() is not new.
    session["modify"] = post_id

    return new_entry(invalid=invalid)


# Delete Post.
@app.route("/delete", methods=["POST"])
@login_required
def delete():
    requested_post_id = request.form.get("post_id")
    this_post = db.session.query(Posts).get(requested_post_id)

    # Get photo name.
    photo_name = this_post.item

    # Delete post.
    post_creator_id = int(this_post.user_id)
    logged_user_id = session["user_id"]
    if logged_user_id == post_creator_id:

        # Remove from favorites every row with this post's ID.
        db.session.query(Favorites).filter(
            Favorites.post_id == requested_post_id).delete()

        # Delete this post.
        db.session.delete(this_post)
        db.session.commit()

        # Remove photo file from 'static'.
        photo_path = os.path.join(
            app.config["UPLOAD_FOLDER"], 'photos', photo_name)
        if os.path.exists(photo_path):
            os.remove(photo_path)

        # Remove thumbnail file from 'static'.
        thumbnail_path = os.path.join(
            app.config["UPLOAD_FOLDER"], 'thumbnails', "thumb_" + photo_name)
        if os.path.exists(thumbnail_path):
            os.remove(thumbnail_path)

        # Remove quote file from 'static'.
        quote_path = os.path.join(
            app.config["UPLOAD_FOLDER"], 'quotes', "quote_" + photo_name.split('.')[0] + ".txt")
        if os.path.exists(quote_path):
            os.remove(quote_path)

    return redirect("/user/posts/")


# Open personal blog.
@app.route("/user/<selection>/")
@login_required
def user(selection):
    id = session["user_id"]
    # Get path details and pass them to posts().
    current_path = request.path
    path_details = {}
    path_details['main'], path_details['sub'] = current_path.strip(
        '/').split('/')
    return posts(id, path_details)


# Display all posts or user's posts, ordered by time of creation, authors, titles or popularity.
@app.route("/all_posts/")
def posts(user_id=None, path_details={'main': 'posts', 'sub': None}):
    # Get from request 'site' argument which defines sorting.
    site = request.args.get('site')
    path_details['site'] = site

    # Get number of the current page.
    page = request.args.get('page', 1, type=int)

    # Define type of selection, which may be: all post or
    # user's posts or collection or recommendations for the user.
    if path_details['main'] == 'posts':
        selection = "all_posts"
    else:
        selection = path_details['sub']

    # Find out the number of all pages for each selection.
    if selection == 'all_posts':
        num_of_posts = Posts.query.count()
    elif selection == "posts":
        num_of_posts = Posts.query.filter_by(user_id=user_id).count()
    elif selection == "collection":
        num_of_posts = Favorites.query.filter_by(user_id=user_id).count()
    elif selection == "recommendations":
        # Select posts recommended for the user.

        # Create a set of users who chose the posts chosen by the user.
        users_choice = set(
            x.post_id for x in Favorites.query.filter_by(user_id=user_id).all())
        users_who_chose_the_same = set()
        for post_id in users_choice:
            users_who_chose_the_post = set(x.user_id for x in Favorites.query.filter_by(
                post_id=post_id).all() if x.user_id != user_id)
            users_who_chose_the_same |= users_who_chose_the_post

        # Create `points_dict` where the keys are ids of `users_who_chose_the_same` and the values are points.
        points_dict = {}
        for a_user in users_who_chose_the_same:
            a_users_likes = set(
                x.post_id for x in Favorites.query.filter_by(user_id=a_user).all())

            # A_user gets one point for each post they've chosen that corresponds to the user's choice.
            a_users_points = len(users_choice & a_users_likes)
            # The rest of a_user's chosen posts are weight accordingly to the number of collected points.
            # The posts created by the user also have to be removed from the list.
            users_posts = set(
                x._id for x in Posts.query.filter_by(user_id=user_id).all())
            a_user_distinct_likes = a_users_likes - users_choice - users_posts
            for post in a_user_distinct_likes:
                points_dict.setdefault(post, 0)
                points_dict[post] += a_users_points

        # Sort selected posts first by points then by id (which also tells when the post was added).
        sorted_by_points_list = sorted(
            sorted(points_dict, reverse=True), key=points_dict.get, reverse=True)

        # Finally count the posts.
        num_of_posts = Posts.query.filter(
            Posts._id.in_(sorted_by_points_list)).count()

    # Count the number of pages necessary to display all posts.
    div, mod = divmod(num_of_posts, app.config["ITEMS_PER_PAGE"])
    num_of_pages = div + bool(mod)

    # Create list of pages with ellipses to pass it to the 'pagi' (pagination) macro in 'help.html'.
    pages = []
    def show_page(x): return bool(x == 1 or x == num_of_pages or x in range(
        page - app.config["LEFT_CURRENT"], page + app.config["RIGHT_CURRENT"]))
    for number in range(1, num_of_pages + 1):
        if show_page(number):
            pages.append(number)
        elif show_page(number + 1):
            pages.append(False)

    # Get required posts.
    slice_of_base = Posts.query
    if selection == "posts":
        slice_of_base = slice_of_base.filter_by(user_id=user_id)
    elif selection == "collection":
        slice_of_base = slice_of_base.filter(
            Posts.favorites.any(user_id=user_id))

    # Sort posts according to the 'site' argument.
    if site == 'latest':
        slice_of_base = slice_of_base.order_by(Posts.added.desc())
    elif site == 'most_popular':
        slice_of_base = slice_of_base.join(
            Favorites, isouter=True).group_by(Posts).order_by(func.count(Favorites.post_id).desc(), Posts.added.desc())
    elif site == "authors":
        slice_of_base = slice_of_base.join(Authors).order_by(Authors.name)
    elif site == "titles":
        slice_of_base = slice_of_base.join(
            Titles).order_by(func.lower(Titles.title))

    # Define offset (limit comes from app.config).
    offset = (page - 1) * app.config["ITEMS_PER_PAGE"]

    # Take slice of database. Use offset and limit methods in all cases, except for "recommendations"
    # where slice of the list is used to get required piece of database.
    if selection == "recommendations":
        current_dbase = [Posts.query.get(
            x) for x in sorted_by_points_list[offset:offset + app.config["ITEMS_PER_PAGE"]]]
    else:
        slice_of_dbase = slice_of_base.offset(
            offset).limit(app.config["ITEMS_PER_PAGE"])
        current_dbase = slice_of_dbase.all()

    # Create posts dictionary containing all the data needed by posts.html
    posts = {
        "page": page,
        "pages": pages or [1],
        "current_dbase": [post_details_dict(x._id, scope=('author', 'title', 'thumbnail', 'quote', 'marker')) for x in current_dbase],
    }

    return render_template("posts.html", posts=posts, path_details=path_details)


@app.route("/post/")
def display_post(id=None):

    id = id or request.args.get('p')
    # Send other posts' coordinates
    coordinates = []
    all_posts = Posts.query.all()
    for p in all_posts:
        if p.place:
            dic = post_details_dict(p._id, scope=(
                'author', 'title', 'latitude', 'longitude'))
            coordinates.append(dic)

    post = post_details_dict(id)

    # Create dictionary `logged_user` to pass to 'post.html' information
    # if the user is logged in and whether the post is in the user's collection.
    user_id = session.get("user_id", None)
    logged_user = {"user_id": user_id}
    if user_id:
        in_collection = bool(Favorites.query.filter_by(
            user_id=user_id, post_id=id).first())
        logged_user["in_collection"] = in_collection

    return render_template("post.html", post=post, coordinates=coordinates, logged_user=logged_user)


# Add posts to the collection or remove it.
@app.route("/collection", methods=["POST"])
@login_required
def collection():
    post_id = request.form.get("post_id")

    # 'button_value' starts with 'add' or 'remove' which defines the required action.
    button_value = request.form.get("collection-button")
    if re.search('^Add', button_value):
        new_fav = Favorites(user_id=session["user_id"], post_id=post_id)
        db.session.add(new_fav)
    if re.search('^Remove', button_value):
        del_fav = db.session.query(Favorites).filter_by(
            user_id=session["user_id"], post_id=post_id).first()
        db.session.delete(del_fav)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
    finally:
        current_page = request.form.get("current-page")
        return redirect(current_page)


# Respond to the search query send from the home page.
@app.route("/search/")
def search():
    phrase = request.args.get('q').casefold()

    # Check if the query is long enough.
    if len(phrase) > 2:
        search_phrase = f'%{phrase}%'
        # Create dictionary for categories: Author, Title, Quote, Place, User.
        posts = {}

        # Search in authors.
        posts["authors"] = Posts.query.join(
            Authors).filter(Authors.name.like(search_phrase)).all()

        # Search in titles.
        posts["titles"] = Posts.query.join(Titles).filter(
            Titles.title.like(search_phrase)).all()

        # Search in users.
        posts["users"] = Posts.query.join(Users).filter(
            Users.username.like(search_phrase)).all()

        # Search in quotes.
        basepath = os.path.join(app.config["UPLOAD_FOLDER"], 'quotes')
        posts['quotes'] = []
        # Read every quote stored in the 'quotes' directory.
        for quote_file in os.listdir(basepath):
            quote = os.path.join(basepath, quote_file)
            with open(quote) as q:
                text = q.read()
                if phrase in text.casefold():
                    # Identify post and add it to the dictionary.
                    prefix = quote_file.split('_', 1)[1].rstrip('.txt')
                    result = Posts.query.filter(
                        Posts.item.startswith(prefix)).first()
                    if result:
                        posts['quotes'].append(result)

        # Search in places.
        # Try to find the place's name as it is stored in Nominatim object.
        place = geolocator.geocode(phrase, namedetails=True)
        try:
            place_name = place.raw['namedetails']['name'].casefold()
        except (KeyError, AttributeError):
            place_name = phrase

        if place_name != phrase:
            posts['places'] = Posts.query.filter(
                (Posts.place.like(f"%{place_name}%")) | (Posts.place.like(f"%{phrase}%"))).all()
        else:
            posts['places'] = Posts.query.filter(
                Posts.place.like(f"%{phrase}%")).all()

        # Create a list of tuples `posts_list`.
        # First element in each tuple is the name of a nonempty category,
        # the second element is a dictionary with id, title, thumbnail address and the text to display.
        for value in posts.values():
            for index, post in enumerate(value):
                new_dict = {}

                # Get post's details.
                this_post_dict = post_details_dict(post._id, scope=(
                    'author', 'title', 'quote', 'thumbnail', 'user', 'place'))

                # Pass to the dictionary data necessary to display results and link them to posts in database.
                new_dict['id'] = this_post_dict['id']
                new_dict['title'] = this_post_dict['title']
                new_dict['thumbnail'] = this_post_dict['thumbnail']

                # Add author and title to the string.
                new_dict['text'] = f"{this_post_dict['author']}, \
                    <i>{this_post_dict['title']}</i>, "

                # If quote is longer than QUOTE_SAMPLE_LENGHT, slice it and add the slice to the string.
                qsl = app.config['QUOTE_SAMPLE_LENGHT']
                this_quote = this_post_dict['quote'].split()

                if len(this_quote) > qsl:
                    if post in posts['quotes']:
                        # Find in quote first instance of the phrase.
                        for i, word in enumerate(this_quote):
                            if phrase in word.casefold():
                                phrase_index = i
                                break

                        # Slice the quote and add ellipsis if needed.
                        if phrase_index > qsl // 2:
                            if phrase_index + (qsl // 2) > len(this_quote):
                                this_quote = ['...'] + this_quote[-qsl:]
                            else:
                                this_quote = ['...'] + \
                                    this_quote[phrase_index - (qsl // 2): phrase_index + (qsl // 2)] + \
                                    ['...']
                        else:
                            this_quote = this_quote[:(qsl)] + ['...']

                    else:
                        this_quote = this_quote[:(qsl)] + ['...']

                new_dict["text"] += '"' + ' '.join(this_quote) + '", '

                # Add bold tags to the text.
                if (post in posts["authors"]) or (post in posts["titles"]) or (post in posts["quotes"]):
                    new_dict["text"] = add_bold_tags(new_dict["text"], phrase)

                # Add place if exists.
                if post in posts['places']:
                    new_dict["text"] += "Place: "
                    this_place = post.place.split(', ')
                    for word in this_place:
                        if phrase in word.casefold() or place_name in word:
                            word = add_bold_tags(word, phrase)
                            word = add_bold_tags(word, place_name)
                            new_dict["text"] += f'{word}, '

                # Add creator's name to the string.
                username = post.user.username
                if post in posts['users']:
                    username = add_bold_tags(username, phrase)
                new_dict["text"] += f"Created by: {username}."

                value[index] = new_dict

        posts_list = []
        for category in posts:
            if posts[category]:
                posts[category].sort(key=lambda x: x['id'], reverse=True)
                # Create two-element tuple with the category's name and list of dictionaries.
                posts_list.append((category, posts[category]),)

        # Sort the list as to display first the category with the most results.
        posts_list.sort(key=lambda x: len(x[1]), reverse=True)

        return render_template("/search.html", posts=posts_list, phrase=phrase)

    return redirect("/")
