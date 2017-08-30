from app.common import hasKeys

class RPI:
	timestamp = None
	humidity = None
	temperature = None
	light = None
	lastmotion = None
	
	leds = None
	dht11_monitor = None
	ldr_monitor = None
	
	def __init__(self, topic, name):
		self.topic = topic
		self.name = name
		
	def setSensorsData(self, payload):
		if hasKeys(payload,['Timestamp','DHT11','LDR']) and hasKeys(payload['DHT11'],['Humidity','Temperature']) and hasKeys(payload['LDR'],['Value']):
			self.timestamp = payload['Timestamp']
			self.humidity = payload['DHT11']['Humidity']
			self.temperature = payload['DHT11']['Temperature']
			self.light = payload['LDR']['Value']
			
	def getSensorsData(self):
		data = {
			'Timestamp': self.timestamp,
			'Humidity': self.humidity,
			'Temperature': self.temperature,
			'Light': self.light
		}
		
		return data
			
	def setControlsData(self, payload):
		if hasKeys(payload,['LEDs','DHT11_Monitor','LDR_Monitor']):
			self.dht11_monitor = payload['DHT11_Monitor']
			self.ldr_monitor = payload['LDR_Monitor']
			
			leds = {}
			for pin,dict in payload['LEDs'].iteritems():
				leds[pin] = {
					'Value': dict['Value'],
					'Overwrite': dict['Overwrite']
				}
				
			self.leds = leds
			
	def getControlsData(self):
		data = {
			'Timestamp': self.timestamp,
			'LEDs': self.leds,
			'DHT11_Monitor': self.dht11_monitor,
			'LDR_Monitor': self.ldr_monitor
		}
		
		return data
		
	def isOverwriteLED(self, pin):
		overwrite = False
		
		leds = self.leds
		if leds and pin in leds:
			led = leds[pin]
			if led['Overwrite']:
				overwrite = True
				
		return overwrite