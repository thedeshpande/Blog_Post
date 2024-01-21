from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey

db = SQLAlchemy()


class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    author = relationship('User', back_populates='posts')
    author_id = db.Column(db.Integer, ForeignKey('users.id'))
    comments = relationship('Comments', back_populates='blog')


class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250))
    email = db.Column(db.String(250), unique=True)
    password = db.Column(db.String(250))
    posts = relationship('BlogPost', back_populates='author')
    comments = relationship('Comments', back_populates='author')


class Comments(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(250))
    author = relationship('User', back_populates='comments')
    author_id = db.Column(db.Integer, ForeignKey('users.id'))
    blog = relationship('BlogPost', back_populates='comments')
    blog_id = db.Column(db.Integer, ForeignKey('blog_posts.id'))

