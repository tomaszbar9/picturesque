import os
from config import Config
from flask import redirect, session
from functools import wraps
from database import Posts


def add_bold_tags(text: str, to_mark: str) -> str:
    """Mark all instances of `to_mark` string in `text` string with html <b> and </b> tags.

    :param str text: Longer string.
    :param str to_mark: Shorter string.
    :return str: String with html bold tags.
    """
    to_mark = to_mark.casefold()
    if to_mark in text.casefold():
        start, sep, _ = text.casefold().partition(to_mark)
        return text[:len(start)] + '<b>' + text[len(start):len(start) + len(sep)] + '</b>' + add_bold_tags(text[len(start) + len(sep):], to_mark)
    else:
        return text


def allowed_files(filename: str) -> bool:
    """Check if the string has an extension part
    and the extension in constant `ALLOWED_EXTENSIONS`.

    :param str filename: The name of a file.
    :return bool: True if the extension is allowed,
        otherwise False.
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


def login_required(f: "function") -> "function":
    """Check if the user is logged in. Prevent unauthorized access
    to the page returned by function `f`.

    :param function f: Function that required logging in.
    :return function: If the user is logged in, return untouched function,
        otherwise redirect to /login.html.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def post_details_dict(id: int, *, scope: tuple = ("all",)) -> dict:
    """Return dictionary containing specific details of the post with given id.

    :param int id: The posts's id.
    :param str scope: Tuple containing names of post's propertis.
        Accepts: 'author', 'title', 'photo', 'thumbnail', 'quote',
        'latitude', 'longitude', 'username', 'user_id', 'place', 
        'marker', defaults to "all"
    :return dictionary with details defined by `scope`.
        Dictionary always has 'id' key with posts'id value.
    """
    post = Posts.query.get(id)
    all_items_tuple = 'author', 'title', 'photo', 'quote', 'latitude', 'longitude', 'username', 'user_id', 'place'

    if "all" in scope:
        scope = all_items_tuple

    # Make dict
    post_dict = {'id': post._id}
    if "author" in scope:
        post_dict['author'] = post.author.name
    if "title" in scope:
        post_dict['title'] = post.title.title
    if "photo" in scope:
        post_dict['photo'] = 'photos/' + post.item
    if "thumbnail" in scope:
        post_dict['thumbnail'] = 'thumbnails/thumb_' + post.item
    if "quote" in scope:
        # Load the quote
        quote_path = os.path.join(
            Config.UPLOAD_FOLDER, 'quotes', 'quote_' + post.item.split('.')[0] + '.txt')
        with open(quote_path, encoding='utf-8') as quote:
            quote_txt = quote.read()
        post_dict['quote'] = quote_txt
    if "latitude" in scope:
        post_dict['latitude'] = post.latitude
    if "longitude" in scope:
        post_dict['longitude'] = post.longitude
    if "username" in scope:
        post_dict['user'] = post.user.username
    if "user_id" in scope:
        post_dict['user_id'] = post.user._id
    if "place" in scope:
        post_dict['place'] = post.place
    if "marker" in scope:
        if post.latitude and post.longitude and post.place:
            post_dict['marker'] = True
        else:
            post_dict['marker'] = False
    return post_dict
