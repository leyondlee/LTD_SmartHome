from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import ConfigParser
import os

__GETCONFIGMAIN_ERROR__ = '''
	[Main]
	Missing field(s) or wrong type.
	Fields must be as follows:
		> topic - STRING
		> button_pin - INTEGER
'''

__GETCONFIGGOOGLE_ERROR__ = '''
	[AWS]
	Missing field(s) or wrong type.
	Fields must be as follows:
		> aws_endpoint - STRING
		> aws_rootcapath - STRING
		> aws_certificatepath - STRING
		> aws_privatekeypath - STRING
'''

__GETCONFIGAWS_ERROR__ = '''
	[AWS]
	Missing field(s) or wrong type.
	Fields must be as follows:
		> aws_endpoint - STRING
		> aws_rootcapath - STRING
		> aws_certificatepath - STRING
		> aws_privatekeypath - STRING
'''

def getConfig():
	dict = {}
	
	config = ConfigParser.ConfigParser()
	config.read('settings.ini')
	if config:
		for s in config.sections():
			d = {}
			for o in config.options(s):
				d[o] = config.get(s,o)
				
			dict[s] = d
	
	return dict
	
def getConfigMain():
	results = {}
	
	dict = getConfig()
	try:
		dict = dict['Main']
		results['topic'] = dict['topic']
		results['button_pin'] = int(dict['button_pin'])
	except:
		print('Exception: {}'.format(e))
		raise ValueError(__GETCONFIGMAIN_ERROR__)
			
	return results
	
def getConfigGoogle():
	results = {}
	
	dict = getConfig()
	try:
		dict = dict['Google']
		results['application_credentials_file'] = dict['application_credentials_file']
	except:
		print('Exception: {}'.format(e))
		raise ValueError(__GETCONFIGGOOGLE_ERROR__)
			
	return results
	
def getConfigAWS():
	results = {}
	
	dict = getConfig()
	try:
		dict = dict['AWS']
		results['aws_endpoint'] = dict['aws_endpoint']
		results['aws_rootcapath'] = dict['aws_rootcapath']
		results['aws_certificatepath'] = dict['aws_certificatepath']
		results['aws_privatekeypath'] = dict['aws_privatekeypath']
	except Exception as e:
		print('Exception: {}'.format(e))
		raise ValueError(__GETCONFIGAWS_ERROR__)
			
	return results
	
def getMQTTClient(name=''):
	mqttClient = None
	
	config = getConfigAWS()
	if config:
		host = config['aws_endpoint']
		rootCAPath = config['aws_rootcapath']
		certificatePath = config['aws_certificatepath']
		privateKeyPath = config['aws_privatekeypath']
		
		mqttClient = AWSIoTMQTTClient(name)
		mqttClient.configureEndpoint(host, 8883)
		mqttClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)
		mqttClient.configureOfflinePublishQueueing(-1)
		mqttClient.configureDrainingFrequency(2)
		mqttClient.configureConnectDisconnectTimeout(10)
		mqttClient.configureMQTTOperationTimeout(5)
		
		try:
			mqttClient.connect()
		except:
			raise ValueError('''
				Unable to connect to AWS.
			''')
	
	return mqttClient
	
def deleteFile(filename):
	if os.path.isfile(filename):
		os.remove(filename)