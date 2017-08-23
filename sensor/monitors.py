from gpiozero import MCP3008
from time import sleep
import threading
import Adafruit_DHT

class DHT11_Monitor(threading.Thread):
	condition = threading.Condition()
	monitor = True
	
	loop = False
	humidity = None
	temperature = None
	
	def __init__(self,pin):
		threading.Thread.__init__(self)
		self.pin = pin
		
	def run(self):
		self.loop = True
		
		while self.loop:
			humidity, temperature = Adafruit_DHT.read_retry(11,self.pin)
			if humidity and temperature:
				self.humidity = humidity
				self.temperature = temperature
				
			sleep(5)
			
			with self.condition:
				if not self.monitor:
					self.humidity = None
					self.temperature = None
					self.condition.wait()
	
	def pause(self):
		self.monitor = False
		
	def resume(self):
		self.monitor = True
		with self.condition:
			self.condition.notifyAll()
		
	def stop(self):
		self.loop = False
		self.resume()
		
class LDR_Monitor(threading.Thread):
	condition = threading.Condition()
	monitor = True
	
	loop = False
	value = None
	
	def __init__(self,channel):
		threading.Thread.__init__(self)
		self.ldr = MCP3008(channel=channel)
		
	def run(self):
		self.loop = True
		
		while self.loop:
			self.value = self.ldr.value
					
			sleep(5)
			
			with self.condition:
				if not self.monitor:
					self.value = None
					self.condition.wait()
		
	def pause(self):
		self.monitor = False
		
	def resume(self):
		self.monitor = True
		with self.condition:
			self.condition.notifyAll()
		
	def stop(self):
		self.loop = False
		self.resume()