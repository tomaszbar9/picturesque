from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config
from datetime import datetime


app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)


class Users(db.Model):
    _id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Text, nullable=False)
    hash = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return '%r' % self.username


class Posts(db.Model):
    _id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users._id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('authors._id'),
                          nullable=False)
    title_id = db.Column(db.Integer, db.ForeignKey('titles._id'),
                         nullable=False)
    item = db.Column(db.String(80), nullable=False)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    place = db.Column(db.Text)
    user = db.relationship("Users", backref=db.backref("posts", lazy=True))
    author = db.relationship("Authors", backref=db.backref("posts", lazy=True))
    title = db.relationship("Titles", backref=db.backref("posts", lazy=True))
    added = db.Column(db.DateTime, nullable=False)

    def __repr__(self):
        return 'Post %r' % self._id


class Authors(db.Model):
    _id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return '%r' % self.name


class Titles(db.Model):
    _id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey(
        'authors._id'), nullable=False)
    author = db.relationship(
        "Authors", backref=db.backref('titles', lazy=True))

    def __repr__(self):
        return '%r' % self.title


class Favorites(db.Model):
    _id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users._id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('posts._id'), nullable=False)
    user = db.relationship(
        "Users", backref=db.backref('favorites'), lazy=True)
    post = db.relationship(
        "Posts", backref=db.backref('favorites'), lazy=True)
    added = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


db.create_all()
