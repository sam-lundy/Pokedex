from flask_wtf import FlaskForm
from wtforms import StringField, EmailField, PasswordField, SubmitField, ValidationError
from wtforms.validators import DataRequired, EqualTo
from app.models import User


class LoginForm(FlaskForm):
    user_or_email = StringField('Username/Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')

class RegisterForm(FlaskForm):
    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already taken.')

    name = StringField('Name', validators=[DataRequired()])             
    email = EmailField('Email Address', validators=[DataRequired()])
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password: ', validators=[DataRequired()])
    password_conf = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired()])
    new_password_conf = PasswordField('Confirm New Password', validators=[
        DataRequired(),
        EqualTo('new_password', message='Passwords must match.')  # Ensures the new password and its confirmation match
    ])
    submit = SubmitField('Change Password')
