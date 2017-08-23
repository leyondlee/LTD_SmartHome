from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField
from wtforms.validators import Required, Regexp, NumberRange

class AddRoomForm(FlaskForm):
	topic = StringField('Topic', validators=[
		Required(message='Must provide topic.'),
		Regexp('^[a-zA-Z0-9]+$', message="Topic must be alphanumeric.")
	])
	displayname = StringField('Display Name', validators=[Required(message='Must provide displayname.')])
	nightlevel = IntegerField('Night Level', validators=[
		NumberRange(0, 1024, message='Night level must be between 0 and 1024.')
	])