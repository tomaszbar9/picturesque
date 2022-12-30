import os
import datetime
import random
from PIL import Image
from database import db, Authors, Favorites, Posts, Titles, Users

# Folder with photos to populate the database.
main_path = 'cs50_photos'
paths = os.listdir(main_path)

# Number of users currently registered.
number_of_users = Users.query.count()

# Get words used in users, titles and authors to work them into lorem ipsum quote.
from_db = [x.username for x in Users.query.all()] + \
    [x.title for x in Titles.query.all()] + \
    [x.name for x in Authors.query.all()]
articles = ['a', 'an', 'the']
keywords = [y for x in from_db for y in x.split() if y.casefold()
            not in articles]
quote = "Lorem ipsum dolor sit amet, consectetur adipisci elit, sed eiusmod tempor incidunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrum exercitationem ullam corporis suscipit laboriosam, nisi ut aliquid ex ea commodi consequatur. Quis aute iure reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur."

# Loop through photos, saving them in database.
for x in paths:
    path = os.path.join(main_path, x)
    with Image.open(path) as img:
        # Create timestamp.
        added_time = datetime.datetime.utcnow()
        time_string = added_time.strftime('%y%m%d%H%M%S')

        # Extract extension.
        ext = x.rsplit('.', 1)[1].lower()

        # Get random title and random user.
        title = random.choice(Titles.query.all())
        user_id = random.randint(1, number_of_users)

        # Create filename and make sure if is unique.
        item = f"{str(user_id)}_{time_string}"
        while item + '.' + ext in {x.item for x in Posts.query.all()}:
            segments = item.split('_')
            number_of_segments = len(segments)
            if number_of_segments > 2:
                segments[-1] = str(int(segments[-1]) + 1)
            else:
                segments.append('1')
            item = '_'.join(segments)

        # Save photo and thumnail (in this case both the same quality).
        photo_path = os.path.join('static', 'photos', item + '.' + ext)
        img.save(photo_path, quality=50)
        thumbnail_path = os.path.join(
            'static', 'thumbnails', "thumb_" + item + '.' + ext)
        img.save(thumbnail_path, quality=50)

        # Place one random keyword somewhere in the quote.
        a_word = random.choice(keywords)
        quote_splited = quote.split()
        word_place = random.randint(0, len(quote_splited))
        quote_splited.insert(word_place, a_word)
        new_quote = ' '.join(quote_splited)

        # Save quote.
        quote_path = os.path.join('static', 'quotes', "quote_" + item + '.txt')
        with open(quote_path, 'w', encoding='utf-8', newline='') as q:
            q.write(new_quote)

        # Place marker somewhere near to Dublin center.
        # There's a 33% chance that the post will be marked.
        place_marker = random.randint(1, 3)
        if place_marker == 1:
            # Dublin's coordinates
            central_lat = 53.3498006
            central_long = -6.2602964
            place = 'Dublin'
            # Find new coordinates.
            latitude = round(
                central_lat + random.randint(-500000, 500000) / 10000000, 7)
            longitude = round(
                central_long + random.randint(-500000, 500000) / 10000000, 7)
        else:
            place = None
            latitude = None
            longitude = None

        # Add new post.
        new = Posts(user_id=user_id, author_id=title.author._id, title_id=title._id,
                    item=item + '.' + ext, added=added_time, latitude=latitude, longitude=longitude, place=place)
        db.session.add(new)
        db.session.flush()

        # Add this post to some of the collections.
        num_of_likes = random.randint(1, number_of_users)
        users_who_like = [x for x in random.sample(
            range(1, number_of_users + 1), num_of_likes) if x != user_id]
        for u in users_who_like:
            new_fav = Favorites(user_id=u, post_id=new._id)
            db.session.add(new_fav)

db.session.commit()
