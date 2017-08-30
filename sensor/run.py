from lib import getConfigMain, getLEDs, getMQTTClient
from monitors import DHT11_Monitor, LDR_Monitor
from signal import pause
from time import sleep
from gpiozero import MotionSensor
import threading
import json
import time
import os

configMain = getConfigMain()
topic = configMain['topic']
dht11_pin = configMain['dht11_pin']
motionsensor_pin = configMain['motionsensor_pin']
ldr_channel = configMain['ldr_channel']
led_pins = configMain['led_pins']

leds = getLEDs(led_pins)

if topic:
	topic = 'room/{}'.format(topic)
	motion_topic = '{}/motion'.format(topic)
	sensors_topic = '{}/sensors'.format(topic)
	controls_topic = '{}/controls'.format(topic)
else:
	print('Error: No topic provided. Please specify a topic in settings.')
	os._exit(0)

class MQTT_Handler(threading.Thread):
	loop = False
	
	def __init__(self):
		threading.Thread.__init__(self)
		
	def run(self):
		self.loop = True
		
		while self.loop:
			publish()
			
			sleep(10)
			
	def stop(self):
		self.loop = False
		
def publish():
	global leds, mqttClient, dht11_monitor, ldr_monitor
	
	timestamp = time.time()
	
	sensors = {
		'Timestamp': timestamp,
		'DHT11': {
			'Humidity': dht11_monitor.humidity,
			'Temperature': dht11_monitor.temperature
		},
		'LDR': {
			'Value': ldr_monitor.value
		}
	}
	
	led_dict = {}
	for pin,dict in leds.iteritems():
		led_dict[pin] = {
			'Value': dict['LED'].value,
			'Overwrite': dict['Overwrite']
		}
	
	controls = {
		'LEDs': led_dict,
		'DHT11_Monitor': dht11_monitor.monitor,
		'LDR_Monitor': ldr_monitor.monitor
	}
	
	mqttClient.publish(sensors_topic,json.dumps(sensors),1)
	mqttClient.publish(controls_topic,json.dumps(controls),1)

def mqttCallback(client, userdata, message):
	global leds, dht11_monitor, ldr_monitor
	
	topic = message.topic
	payload = json.loads(message.payload)
	
	parts = topic.split('/')
	
	if len(parts) == 5:
		subtype = parts[3]
		param = parts[4]
		
		valid = True
		if subtype == 'led':
			value = payload['Value']
			overwrite = payload['Overwrite']
			
			if param == 'all':
				if 0 <= value <= 1:
					for key,dict in leds.iteritems():
						dict['LED'].value = value
						dict['Overwrite'] = overwrite
			else:
				param = int(param)
				
				if 0 <= value <= 1:
					if param in leds:
						led = leds[param]
						led['LED'].value = value
						led['Overwrite'] = overwrite
		elif subtype == 'process':
			value = payload['Value']
			
			if param == 'dht11':
				if value:
					dht11_monitor.resume()
				else:
					dht11_monitor.pause()
			elif param == 'ldr':
				if value:
					ldr_monitor.resume()
				else:
					ldr_monitor.pause()
		else:
			valid = False
		
		if valid:
			publish()
		
def motion_detected():
	global mqttClient, motion_topic
	
	timestamp = time.time()
	data = {
		'Timestamp': timestamp
	}
	
	mqttClient.publish(motion_topic,json.dumps(data),1)

mqttClient = getMQTTClient()
mqttClient.subscribe('{}/controls/#'.format(topic), 1, mqttCallback)
		
dht11_monitor = DHT11_Monitor(dht11_pin)
ldr_monitor = LDR_Monitor(ldr_channel)
mqtthandler = MQTT_Handler()

dht11_monitor.start()
ldr_monitor.start()
mqtthandler.start()

pir = MotionSensor(motionsensor_pin)
pir.when_motion = motion_detected

try:
	pause()
except KeyboardInterrupt:
	os._exit(0)