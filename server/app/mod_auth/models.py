from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, Base
import hashlib
import uuid
import time

class User(Base, UserMixin):
	__tablename__ = 'User'
	
	username = db.Column(db.String(100), primary_key=True)
	passwordhash = db.Column(db.String(93), nullable=False)
	apikey = db.Column(db.String(64), nullable=True)
	
	def __init__(self, username):
		self.username = username
		
	def __repr__(self):
		return '<User {}>'.format(self.username)
		
	def get_id(self):
		return self.username
		
	def set_password(self, password):
		self.passwordhash = generate_password_hash(password,method='pbkdf2:sha256')
		self.save()
		
	def check_password(self, password):
		return check_password_hash(self.passwordhash, password)
		
	def generateApiKey(self):
		m = hashlib.sha256()
		m.update(self.username.encode('utf-8'))
		m.update(uuid.uuid4().hex.encode('utf-8'))
		m.update(str(time.time()).encode('utf-8'))
		
		apikey = m.hexdigest()
		if User.query.filter_by(apikey=apikey).first():
			generateApiKey(self)
		else:
			self.apikey = apikey
			self.save()
				
	def deleteApiKey(self):
		self.apikey = None
		self.save()