from lib import getConfigMain, getMQTTClient
from rpi_lcd import LCD
from signal import pause
import os
import json

configMain = getConfigMain()
topic = configMain['topic']

if topic:
	topic = 'room/{}/sensors'.format(topic)
else:
	print('Error: No topic provided. Please specify a topic in settings.')
	os._exit(0)

lcd = LCD()
lcd.clear()

def mqttCallback(client, userdata, message):
	global lcd
	
	payload = json.loads(message.payload)
	
	if ('DHT11' in payload and 'LDR' in payload):
		dht11 = payload['DHT11']
		ldr = payload['LDR']
		
		temperature = dht11['Temperature']
		humidity = dht11['Humidity']
		light = ldr['Value']
		
		if temperature and humidity:
			dht11 = '{}{}C, {}%'.format(int(temperature),chr(223),int(humidity))
		else:
			dht11 = '-'
			
		if light:
			ldr = int(round((1024 / light) % 1024))
		else:
			ldr = '-'
		
		lcd.text('DHT: {}'.format(dht11), 1)
		lcd.text('LDR: {}'.format(ldr), 2)
		
mqttClient = getMQTTClient()
mqttClient.subscribe(topic, 1, mqttCallback)

try:
	pause()
except KeyboardInterrupt:
	lcd.clear()