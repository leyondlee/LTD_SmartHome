from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types
from gpiozero import Button
from lib import getConfigMain, getConfigGoogle, getMQTTClient, deleteFile
from signal import pause
from rpi_lcd import LCD
from time import sleep
import subprocess
import re
import json
import os
import signal

configMain = getConfigMain()
topic = configMain['topic']
button_pin = configMain['button_pin']

configGoogle = getConfigGoogle()
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = configGoogle['application_credentials_file']

if topic:
	topic = 'room/{}'.format(topic)
	controls_topic = '{}/controls'.format(topic)
	led_topic = '{}/led/all'.format(controls_topic)
	process_topic = '{}/process'.format(controls_topic)
else:
	print('Error: No topic provided. Please specify a topic in settings.')
	os._exit(0)

class Record():
	process = None
	
	def __init__(self):
		pass
		
	def start(self):
		global lcd
		
		cmd = ['arecord','-r','16000','-f','S16_LE','-D','plughw:1,0','-d','10','output.wav']
		with open(os.devnull,'w') as devnull:
			self.process = subprocess.Popen(cmd,stdout=devnull,stderr=subprocess.STDOUT)
		setTextLCD('Recording...','Release to stop')
		
	def stop(self):
		self.process.kill()

def speechToText(filename):
	texts = []
	
	try:
		client = speech.SpeechClient()
		
		with open(filename,'rb') as f:
			content = f.read()
			audio = types.RecognitionAudio(content=content)
			
		config = types.RecognitionConfig(encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,sample_rate_hertz=16000,language_code='en-US')
		
		response = client.recognize(config,audio)
		results = response.results
		if results:
			alternatives = results[0].alternatives
			
			for alternative in alternatives:
				texts.append(alternative.transcript)
	except:
		pass
		
	return texts
	
def interpretText(text):
	global mqttClient
	
	text = text.lower()
	
	patterns = [
		r'(.*)?(on|off)(.*)?(temperature|humidity|light|all)\ssensor(s)?',
		r'(.*)?(on|off)(.*)?\slight(s)?',
		r'(.*)?light(s)?(.*)?(auto|manual)'
	]
	
	index = None
	search = None
	for i,p in enumerate(patterns):
		search = re.search(p,text)
		if search:
			index = i
			break
	
	if search:
		success = True
		
		if index == 0:
			mode = search.group(2)
			sensor = search.group(4)
			
			if mode == 'on':
				value = True
			else:
				value = False
				
			data = {
				'Value': value
			}
			
			if sensor == 'all':
				data = json.dumps(data)
				mqttClient.publish('{}/dht11'.format(process_topic),data,1)
				mqttClient.publish('{}/ldr'.format(process_topic),data,1)
			else:
				if sensor == 'temperature' or sensor == 'humidity':
					t = '{}/dht11'.format(process_topic)
				else:
					t = '{}/ldr'.format(process_topic)
					
				mqttClient.publish(t,json.dumps(data),1)
		elif index == 1:
			mode = search.group(2)
			
			if mode == 'on':
				value = 1
			else:
				value = 0
			
			data = {
				'Value': value,
				'Overwrite': True
			}
			mqttClient.publish(led_topic,json.dumps(data),1)
		elif index == 2:
			mode = search.group(4)
			
			if mode == 'manual':
				overwrite = True
			else:
				overwrite = False
				
			data = {
				'Value': 0,
				'Overwrite': overwrite
			}
			mqttClient.publish(led_topic,json.dumps(data),1)
	else:
		success = False
		
	return success
	
def buttonPressed():
	global record
	
	if not record:
		record = Record()
		record.start()
	
def buttonReleased():
	global record
	
	setTextLCD('Loading...')
	
	if record:
		record.stop()
		texts = speechToText('output.wav')
		
		accept = False
		for text in texts:
			if interpretText(text):
				accept = True
				
		if accept:
			setTextLCD('Command Accepted')
		else:
			setTextLCD('Unknown Command')
			
		deleteFile('output.wav')
			
		sleep(1)
			
		record = None
	
	ready()
		
def ready():
	global lcd
	
	setTextLCD('Ready to accept','commands')
	
def setTextLCD(top=None,bottom=None):
	global lcd
	
	lcd.clear()
	if top:
		lcd.text(top,1)
		
	if bottom:
		lcd.text(bottom,2)

lcd = LCD()
setTextLCD('Loading...')

mqttClient = getMQTTClient()
record = None

button = Button(button_pin, pull_up=False)
button.when_pressed = buttonPressed
button.when_released = buttonReleased

ready()

try:
	pause()
except KeyboardInterrupt:
	lcd.clear()