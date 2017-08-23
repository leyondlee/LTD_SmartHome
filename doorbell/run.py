from lib import getConfigMain, getMQTTClient
from gpiozero import Buzzer, Button
from signal import pause
from time import sleep
import time
import json

configMain = getConfigMain()
buzzer_pin = configMain['buzzer_pin']
button_pin = configMain['button_pin']

bz = Buzzer(buzzer_pin)
button = Button(button_pin, pull_up=False)

def buzzON():
	data = {
		'Timestamp': time.time()
	}
	mqttClient.publish('doorbell',json.dumps(data),1)
	
	bz.on()
	sleep(0.3)
	bz.off()

mqttClient = getMQTTClient()

button.when_pressed = buzzON

try:
	pause()
except KeyboardInterrupt:
	pass