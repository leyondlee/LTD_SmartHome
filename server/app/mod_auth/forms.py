from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import Required, EqualTo

class LoginForm(FlaskForm):
	username = StringField('Username', validators=[Required(message='Must provide username.')])
	password = PasswordField('Password', validators=[Required(message='Must provide password.')])
	rememberme = BooleanField('Remember me')
	
class ChangePasswordForm(FlaskForm):
	currentpassword = PasswordField('Current Password', validators=[Required(message='Must provide current password.')])
	newpassword = PasswordField('New Password', validators=[
		Required(message='Must provide password.'),
		EqualTo('confirmpassword', message='Passwords do not match.')
	])
	confirmpassword = PasswordField('Confirm Password', validators=[Required(message='Must confirm password.')])