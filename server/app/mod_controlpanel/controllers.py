from flask import Blueprint, render_template, Response, make_response, redirect, url_for
from app.mod_controlpanel.models import Image
from app.common import doVisualRecognition, deleteFile, getConfigCamera, getImage, getStreamStatus
from app.dynamodblib import DecimalEncoder
from app.mqttlib import setLEDValue, setProcessValue
import app.mod_main as main_mod
import app.mod_controlpanel as controlpanel_mod
import json
import base64
import app
import time

mod_controlpanel = Blueprint('controlpanel', __name__, url_prefix='/controlpanel')

@mod_controlpanel.route('/')
def controlpanel():
	stream_address = getConfigCamera()['stream_address']
	rooms = app.rooms
	
	templateData = {
		'stream_address': stream_address,
		'rooms': rooms
	}
	
	return render_template('controlpanel/controlpanel.html', **templateData)
	
@mod_controlpanel.route('/stream')
def streamstatus():
	return json.dumps({'Status': getStreamStatus()})
	
@mod_controlpanel.route('/room', defaults={'room': None})
@mod_controlpanel.route('/room/<room>')
def room(room):
	rooms = app.rooms
	
	if room in rooms:
		rpi = rooms[room]
		response = json.dumps(rpi.getControlsData())
	else:
		response = ('',404)
		
	return response
	
@mod_controlpanel.route('/room/emit', defaults={'room': None, 'socketid': None})
@mod_controlpanel.route('/room/emit/<room>/<socketid>')
def roomemit(room,socketid):
	rooms = app.rooms
	
	if room in rooms:
		rpi = rooms[room]
		app.socketio.emit(room,rpi.getControlsData(),room=socketid)
		response = ('',204)
	else:
		response = ('',404)
		
	return response
	
@mod_controlpanel.route('/room/<room>/led/<int:pin>/set/mode/<int:value>')
def setLEDmode(room,pin,value):
	value = value == 1
	
	rooms = app.rooms
	if room in rooms:
		rpi = rooms[room]
		leds = rpi.leds
		pin = str(pin)
		if leds and pin in leds:
			leds[pin]['Overwrite'] = value
	
	return ('',204)

@mod_controlpanel.route('/room/<room>/led/<int:pin>/set/<int:value>')
@mod_controlpanel.route('/room/<room>/led/<int:pin>/set/<float:value>')
def setLED(room,pin,value):
	setLEDValue(room,pin,value,True)
	
	return ('',204)
	
@mod_controlpanel.route('/room/<room>/process/<process>/set/<value>')
def setProcess(room,process,value):
	setProcessValue(room,process,value)
	
	return ('',204)
	
@mod_controlpanel.route('/camera/image/<int:id>/visualrecognition')
def visualrecognition(id):
	image = Image.query.get(id)
	
	if image:
		img = image.image
		
		timestring = time.strftime("%Y%m%d%H%M%S", time.gmtime())
		filename = 'image_{}.jpg'.format(timestring)

		with open(filename,'wb') as file:
			file.write(img)
			
		results = doVisualRecognition(filename)
		deleteFile(filename)
		
		classes = results['images'][0]['classifiers'][0]['classes']
		
		image.results = json.dumps(classes)
		image.save()
	
		response = ('',204)
	else:
		response = ('',404)
	
	return response
	
@mod_controlpanel.route('/camera/image', defaults={'id': None})
@mod_controlpanel.route('/camera/image/<int:id>')
def camera_image(id):
	image = Image.query.get(id)
	
	if image:
		img = image.image
		response = make_response(img)
		response.headers['Content-Type'] = 'image/jpeg'
	else:
		response = ('', 404)
		
	return response
	
@mod_controlpanel.route('/camera/image/delete', defaults={'id': None})
@mod_controlpanel.route('/camera/image/delete/<int:id>')
def delete_image(id):
	image = Image.query.get(id)
	
	if image:
		image.delete()
		
	return ('',204)
	
@mod_controlpanel.route('/camera/image/<int:id>/details')
def camera_details(id):
	image = Image.query.get(id)
	
	if image:
		timestamp = image.timestamp
		results = image.results
		
		response = json.dumps({
			'ID': id,
			'Timestamp': timestamp,
			'Results': results
		}, cls=DecimalEncoder)
	else:
		response = ('', 404)
		
	return response
	
@mod_controlpanel.route('/camera/capture')
def camera_capture():
	img = getImage()
	
	if img:
		timestamp = time.time()
		image = Image(timestamp,img)
		image.add()
		
		response = json.dumps({'ID':image.id})
	else:
		response = ('', 503)
		
	return response
	
@mod_controlpanel.route('/camera/history')
def camera_history():
	images = Image.query.all()
	
	list = []
	for r in images:
		id = r.id
		timestamp = r.timestamp
		results = r.results
		
		if results:
			results = json.loads(results)
		
		d = {
			'ID': id,
			'Timestamp': timestamp,
			'Results': results
		}
		list.append(d)
		
	return json.dumps(list, cls=DecimalEncoder)