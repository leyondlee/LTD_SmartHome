from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from app.common import getConfigAWS, getSubscription, convertLight, datetimeToTimestamp, getImage
from app.mod_controlpanel.models import Image
from rpi import RPI
import app
import json
import datetime

def getMQTTClient(name=''):
	mqttClient = None
	
	config = getConfigAWS()
	if config:
		host = config['aws_iot_endpoint']
		rootCAPath = config['aws_iot_rootcapath']
		certificatePath = config['aws_iot_certificatepath']
		privateKeyPath = config['aws_iot_privatekeypath']
		
		mqttClient = AWSIoTMQTTClient(name)
		mqttClient.configureEndpoint(host, 8883)
		mqttClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)
		mqttClient.configureOfflinePublishQueueing(-1)
		mqttClient.configureDrainingFrequency(2)
		mqttClient.configureConnectDisconnectTimeout(10)
		mqttClient.configureMQTTOperationTimeout(5)
		
		try:
			mqttClient.connect()
		except Exception as e:
			print(e)
			raise ValueError('''
				Unable to connect to AWS.
			''')
	
	return mqttClient
	
def mqttCallback(client, userdata, message):
	rooms = app.rooms
	
	topic = message.topic
	payload = json.loads(message.payload)
	
	parts = topic.split('/')
	
	if len(parts) == 3:
		room = parts[1]
		type = parts[2]
		
		if room in rooms:
			socketio = app.socketio
			
			rpi = rooms[room]
			if type == 'sensors':
				rpi.setSensorsData(payload)
				socketio.emit(room,rpi.getSensorsData(),room='sensors')
				
				light = rpi.light
				if light:
					subscription = getSubscription(rpi.topic)
					nightlevel = subscription['Nightlevel']
					leds = rpi.leds
					if leds:
						lastmotion = rpi.lastmotion
						if convertLight(light) > nightlevel or not lastmotion or lastmotion < datetimeToTimestamp(datetime.datetime.now() - datetime.timedelta(seconds=30)):
							for pin,d in leds.iteritems():
								value = d['Value']
								overwrite = d['Overwrite']
								if value != 0 and not overwrite:
									setLEDValue(room,pin,0)
			elif type == 'controls':
				rpi.setControlsData(payload)
				socketio.emit(room,rpi.getControlsData(),room='controls')
			elif type == 'motion':
				lastmotion = payload['Timestamp']
				rpi.lastmotion = lastmotion
				
				light = rpi.light
				if light:
					subscription = getSubscription(rpi.topic)
					nightlevel = subscription['Nightlevel']
					if convertLight(light) <= nightlevel:
						leds = rpi.leds
						if leds:
							for pin,d in leds.iteritems():
								value = d['Value']
								overwrite = d['Overwrite']
								if value != 1 and not overwrite:
									setLEDValue(room,pin,1)
									
							socketio.emit(room,rpi.getControlsData(),room='controls')
	
def roomSubscribe(topic):
	subscription = getSubscription(topic)
	
	if subscription:
		topicname = subscription['Topic']
		displayname = subscription['Displayname']
		
		rpi = RPI(topicname,displayname)
		app.rooms[topicname] = rpi
		
		mqttClient = app.mqttClient
		topic = 'room/{}/#'.format(topicname)
		mqttClient.subscribe(topic, 1, mqttCallback)
	
def roomUnsubscribe(topic):
	topicname = topic
	
	mqttClient = app.mqttClient
	topic = 'room/{}/#'.format(topic)
	mqttClient.unsubscribe(topic)
	
	app.rooms.pop(topicname,None)
	
def setLEDValue(room,pin,value,overwrite=False):
	rooms = app.rooms
	mqttClient = app.mqttClient
	
	if room in rooms:
		rpi = rooms[room]
		leds = rpi.leds
		pin = str(pin)
		
		if leds and pin in leds:
			leds[pin]['Value'] = value
			leds[pin]['Overwrite'] = overwrite
			
			topic = 'room/{}/controls/led/{}'.format(room,pin)
			data = {
				'Value': value
			}
			mqttClient.publish(topic,json.dumps(data),1)
			
def setProcessValue(room,process,value):
	rooms = app.rooms
	mqttClient = app.mqttClient
	
	if room in rooms:
		rpi = rooms[room]
		
		value = (value == 'ON')
		
		valid = True
		if process == 'dht11':
			rpi.dht11_monitor = value
		elif process == 'ldr':
			rpi.ldr_monitor = value
		else:
			valid = False
			
		if valid:
			topic = 'room/{}/controls/process/{}'.format(room,process)
			data = {
				'Value': value
			}
			mqttClient.publish(topic,json.dumps(data),1)
			
def doorbellCallback(client, userdata, message):
	payload = json.loads(message.payload)
	
	if 'Timestamp' in payload:
		timestamp = payload['Timestamp']
		
		img = getImage()
		if img:
			image = Image(timestamp,img)
			image.add()