from flask import Flask, render_template, redirect, url_for, request, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from flask_login import LoginManager, current_user
from flask_socketio import SocketIO, emit, disconnect, join_room
import functools
import base64
import boto3

app = Flask(__name__)
app.config.from_object('config')

csrf = CSRFProtect(app)
db = SQLAlchemy(app)
socketio = SocketIO(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

class Base(db.Model):
	__abstract__ = True
	
	def add(self):
		try:
			db.session.add(self)
			self.save()
		except:
			pass

	def save(self):
		try:
			db.session.commit()
		except:
			db.session.rollback()
			
	def delete(self):
		try:
			db.session.delete(self)
			self.save()
		except:
			pass

from app.mod_main.controllers import mod_main as main_mod
app.register_blueprint(main_mod)

from app.mod_controlpanel.controllers import mod_controlpanel as controlpanel_mod
app.register_blueprint(controlpanel_mod)

from app.mod_settings.controllers import mod_settings as settings_mod
app.register_blueprint(settings_mod)

from app.mod_auth.controllers import mod_auth as auth_mod
app.register_blueprint(auth_mod)

db.create_all()

from app.mod_auth.models import User
from app.mqttlib import getMQTTClient, mqttCallback, roomSubscribe, doorbellCallback
from app.common import getConfigAWS, createSensorTable, createSubscriptionTable
from app.dynamodblib import scan
import json

__AWSCONFIG__ = getConfigAWS()
dynamodb = boto3.resource(
	'dynamodb',
	aws_access_key_id=__AWSCONFIG__['aws_webapp_access_key_id'],
    aws_secret_access_key=__AWSCONFIG__['aws_webapp_secret_access_key'],
	region_name=__AWSCONFIG__['aws_webapp_region_name']
)

createSensorTable()
createSubscriptionTable()

mqttClient = getMQTTClient()
mqttClient.subscribe('doorbell', 1, doorbellCallback)

rooms = {}

for s in scan('Subscription'):
	roomSubscribe(s['Topic'])

@login_manager.user_loader
def load_user(user_id):
	return User.query.get(user_id)
	
@app.before_request
def check_login():
	if not request.endpoint or request.endpoint.rsplit('.', 1)[-1] == 'static':
		return
		
	user = current_user
	apikey = request.args.get('apikey')
	if apikey:
		user = User.query.filter_by(apikey=apikey).first()
	else:
		apikey = request.headers.get('Authorization')
		if apikey:
			apikey = apikey.replace('Basic ', '', 1)
			
			user = None
			try:
				apikey = base64.b64decode(apikey)
				user = User.query.filter_by(apikey=apikey).first()
			except:
				pass
		
	view = current_app.view_functions[request.endpoint]
	if not getattr(view,'login_exempt',False):
		if apikey:
			if not user:
				return ('', 401)
		elif not user.is_authenticated:
			return redirect(url_for(login_manager.login_view))
	
@app.route('/')
def index():
	return redirect(url_for('main.index'))
	
def authenticated_only(f):
	@functools.wraps(f)
	def wrapped(*args, **kwargs):
		if not current_user.is_authenticated:
			disconnect()
		else:
			return f(*args, **kwargs)
	return wrapped

@socketio.on('connect')
@authenticated_only
def socket_connect():
	pass
	
@socketio.on('join')
@authenticated_only
def socket_join(message):
	if 'room' in message:
		room = message['room']
		join_room(room)