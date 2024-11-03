# app/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, FloatField, IntegerField
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from .models import User

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('This username is already taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data.lower()).first()
        if user:
            raise ValidationError('This email is already registered. Please choose a different one.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class GenerateTextForm(FlaskForm):
    keywords = StringField('Keywords', validators=[DataRequired(), Length(min=1, max=255)])
    tone = SelectField('Tone', choices=[('neutral', 'Neutral'), ('formal', 'Formal'), ('informal', 'Informal')], validators=[DataRequired()])
    length = SelectField('Length', choices=[('short', 'Short'), ('medium', 'Medium'), ('long', 'Long')], validators=[DataRequired()])
    temperature = FloatField('Temperature', default=0.7, validators=[DataRequired()])
    max_tokens = IntegerField('Max Tokens', default=150, validators=[DataRequired()])
    submit = SubmitField('Generate')

class EditVideoForm(FlaskForm):
    video = FileField('Video', validators=[
        FileRequired(),
        FileAllowed(['mp4', 'avi', 'mov', 'mkv'], 'Video files only!')
    ])
    submit = SubmitField('Edit')

class CreateGraphicForm(FlaskForm):
    template = SelectField('Template', choices=[], validators=[DataRequired()])
    text = StringField('Text', validators=[DataRequired(), Length(min=1, max=255)])
    submit = SubmitField('Create')
