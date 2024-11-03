# app/models.py
from . import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128), nullable=False)

    # Связи
    generated_texts = db.relationship('GeneratedText', backref='author', lazy=True)
    edited_videos = db.relationship('EditedVideo', backref='editor', lazy=True)
    created_graphics = db.relationship('CreatedGraphic', backref='creator', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class GeneratedText(db.Model):
    __tablename__ = 'generated_text'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    keywords = db.Column(db.String(255), nullable=False)
    tone = db.Column(db.String(50), nullable=False)
    length = db.Column(db.String(50), nullable=False)
    temperature = db.Column(db.Float, default=0.7)
    max_tokens = db.Column(db.Integer, default=150)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class EditedVideo(db.Model):
    __tablename__ = 'edited_video'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    edited_filename = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class CreatedGraphic(db.Model):
    __tablename__ = 'created_graphic'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    template = db.Column(db.String(255), nullable=False)
    text = db.Column(db.String(255), nullable=False)
    output_filename = db.Column(db.String(255), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
