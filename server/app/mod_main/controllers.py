from flask import Blueprint, render_template, make_response, request
from sqlalchemy import text
from app.common import getZoom, datetimeToTimestamp, textToSpeech, convertLight
from app.dynamodblib import DecimalEncoder, query
from datetime import datetime
from boto3.dynamodb.conditions import Key
import app.mod_main as main_mod
import json
import app
import urllib

mod_main = Blueprint('main', __name__, url_prefix='/main')

@mod_main.route('/')
def index():
	rooms = app.rooms
	
	templateData = {
		'rooms': rooms
	}
	
	return render_template('main/index.html',**templateData)
	
@mod_main.route('/room', defaults={'room': None})
@mod_main.route('/room/<room>')
def room(room):
	rooms = app.rooms
	
	if room in rooms:
		rpi = rooms[room]
		response = json.dumps(rpi.getSensorsData())
	else:
		response = ('',404)
		
	return response
	
@mod_main.route('/room/emit', defaults={'room': None, 'socketid': None})
@mod_main.route('/room/emit/<room>/<socketid>')
def roomemit(room,socketid):
	rooms = app.rooms
	
	if room in rooms:
		rpi = rooms[room]
		app.socketio.emit(room,rpi.getSensorsData(),room=socketid)
		response = ('',204)
	else:
		response = ('',404)
		
	return response
	
@mod_main.route('/audio', defaults={'room': None})
@mod_main.route('/audio/<room>')
def audio(room):
	rooms = app.rooms
	
	if room in app.rooms:
		rpi = rooms[room]
		data = rpi.getSensorsData()
		
		humidity = data['Humidity']
		temperature = data['Temperature']
		light = data['Light']
		
		messages = []
		if temperature:
			messages.append('The temperature is {} degree celsius.'.format(int(temperature)))
		else:
			messages.append('The temperature cannot be determined.')
			
		if humidity:
			messages.append('The humidity is {} percent.'.format(int(humidity)))
		else:
			messages.append('The humidity cannot be determined.')
			
		if light:
			light = convertLight(light)
			messages.append('The light level is {}.'.format(int(light)))
		else:
			messages.append('The light level cannot be determined.')
			
		message = ' '.join(messages)
		
		audio = textToSpeech(message)
		if audio:
			response = make_response(audio)
			response.headers['Content-Type'] = 'audio/wav'
		else:
			response = ('',503)
	else:
		response = ('',404)
		
	return response
	
@mod_main.route('/history/<room>', defaults={'sensor': None, 'zoom': None})
@mod_main.route('/history/<room>/<sensor>/<int:zoom>')
def history(room,sensor,zoom):
	now = datetime.utcnow()
	startTime = None
	
	columns = None
	expressions = None
	if sensor == 'dht11':
		columns = '#timestamp, Humidity, Temperature'
		expressions = {'#timestamp':'Timestamp'}
	elif sensor == 'ldr':
		columns = '#timestamp, Light'
		expressions = {'#timestamp':'Timestamp'}
	
	zoom = getZoom(zoom)
	if zoom:
		startTime = now - zoom
		
	condition = None
	if startTime:
		condition = Key('Room').eq(room) & Key('Timestamp').between(datetimeToTimestamp(startTime),datetimeToTimestamp(now))
	else:
		condition = Key('Room').eq(room)
		
	results = query('Sensor',condition,columns,expressions)
	results = sorted(results, key=lambda k: k['Timestamp'])
		
	return json.dumps(results, cls=DecimalEncoder)