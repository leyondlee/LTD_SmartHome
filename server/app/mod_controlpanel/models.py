from app import db, Base
from sqlalchemy.dialects.mysql import DOUBLE

class Image(Base):
	__tablename__ = 'Image'
	
	id = db.Column(db.Integer, primary_key=True)
	timestamp = db.Column(DOUBLE, nullable=False)
	image = db.Column(db.BLOB, nullable=False)
	results = db.Column(db.String(1000), nullable=True)
	
	def __init__(self, timestamp, image, results=None):
		self.timestamp = timestamp
		self.image = image
		self.results = results
		
	def __repr__(self):
		return '<Image {}>'.format(self.id)