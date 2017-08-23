from boto3.dynamodb.conditions import Key
from watson_developer_cloud import VisualRecognitionV3, TextToSpeechV1
from dateutil.relativedelta import relativedelta
from dateutil import tz
from datetime import datetime
from app.dynamodblib import createTable, query
import ConfigParser
import os
import app
import ssl
import urllib2
import calendar
import json

__GETCONFIGMAIN_ERROR__ = '''
	[Main]
	Missing field(s) or wrong type.
	Fields must be as follows:
		> debug - BOOLEAN
'''

__GETCONFIGDATABASE_ERROR__ = '''
	[Database]
	Missing field(s) or wrong type.
	Fields must be as follows:
		> db_host - STRING
		> db_port - INTEGER
		> db_user - STRING
		> db_password - STRING
		> db_database - STRING
'''

__GETCONFIGAWS_ERROR__ = '''
	[AWS]
	Missing field(s) or wrong type.
	Fields must be as follows:
		> aws_iot_endpoint - STRING
		> aws_iot_rootcapath - STRING
		> aws_iot_certificatepath - STRING
		> aws_iot_privatekeypath - STRING
		> aws_dynamodb_access_key_id - STRING
		> aws_dynamodb_secret_access_key - STRING
		> aws_dynamodb_region_name - STRING
'''

__GETCONFIGIBM_ERROR__ = '''
	[IBM]
	Missing field(s) or wrong type.
	Fields must be as follows:
		> ibm_visualrecognition_apikey - STRING
		> ibm_texttospeech_username - STRING
		> ibm_texttospeech_password - STRING
'''

__GETCONFIGCAMERA_ERROR__ = '''
	[Camera]
	Missing field(s) or wrong type.
	Fields must be as follows:
		> stream_address - STRING
		> stream_rootcapath - STRING
		> stream_certificatepath - STRING
		> stream_privatekeypath - STRING
		> stream_privatekeypassword - STRING
'''

__GETCONFIGSERVER_ERROR__ = '''
[Server]
Missing field(s) or wrong type.
Fields must be as follows:
	> server_port - INTEGER
	> rootcapath - STRING
	> certificatepath - STRING
	> privatekeypath - STRING
	> privatekeypassword - STRING
'''

def login_exempt(f):
    f.login_exempt = True
    return f
	
def getZoom(zoom):
	if zoom == 1:
		s = relativedelta(minutes=5)
	elif zoom == 2:
		s = relativedelta(minutes=30)
	elif zoom == 3:
		s = relativedelta(hours=1)
	elif zoom == 4:
		s = relativedelta(days=1)
	elif zoom == 5:
		s = relativedelta(weeks=1)
	elif zoom == 6:
		s = relativedelta(months=1)
	elif zoom == 7:
		s = relativedelta(years=1)
	else:
		s = ''
		
	return s
	
def deleteAttribute(object,attr):
	if hasattr(object,attr):
		delattr(object,attr)
	
def getConfigParser():
	configparser = ConfigParser.ConfigParser()
	configparser.read('settings.ini')
	
	return configparser
	
def getConfig():
	dict = {}
	
	configparser = getConfigParser()
	if configparser:
		for s in configparser.sections():
			d = {}
			for o in configparser.options(s):
				d[o] = configparser.get(s,o)
				
			dict[s] = d
	
	return dict
	
def getConfigMain():
	results = {}
	
	dict = getConfig()
	try:
		dict = dict['Main']
		results['debug'] = bool(dict['debug'])
	except Exception as e:
		print('Exception: {}'.format(e))
		raise ValueError(__GETCONFIGMAIN_ERROR__)
			
	return results
	
def getConfigDatabase():
	results = {}
	
	dict = getConfig()
	try:
		dict = dict['Database']
		results['db_host'] = dict['db_host']
		results['db_port'] = int(dict['db_port'])
		results['db_user'] = dict['db_user']
		results['db_password'] = dict['db_password']
		results['db_database'] = dict['db_database']
	except Exception as e:
		print('Exception: {}'.format(e))
		raise ValueError(__GETCONFIGDATABASE_ERROR__)
			
	return results
	
def getConfigAWS():
	results = {}
	
	dict = getConfig()
	try:
		dict = dict['AWS']
		results['aws_iot_endpoint'] = dict['aws_iot_endpoint']
		results['aws_iot_rootcapath'] = dict['aws_iot_rootcapath']
		results['aws_iot_certificatepath'] = dict['aws_iot_certificatepath']
		results['aws_iot_privatekeypath'] = dict['aws_iot_privatekeypath']
		results['aws_dynamodb_access_key_id'] = dict['aws_dynamodb_access_key_id']
		results['aws_dynamodb_secret_access_key'] = dict['aws_dynamodb_secret_access_key']
		results['aws_dynamodb_region_name'] = dict['aws_dynamodb_region_name']
	except Exception as e:
		print('Exception: {}'.format(e))
		raise ValueError(__GETCONFIGAWS_ERROR__)
			
	return results
	
def getConfigIBM():
	results = {}
	
	dict = getConfig()
	try:
		dict = dict['IBM']
		results['ibm_visualrecognition_apikey'] = dict['ibm_visualrecognition_apikey']
		results['ibm_texttospeech_username'] = dict['ibm_texttospeech_username']
		results['ibm_texttospeech_password'] = dict['ibm_texttospeech_password']
	except Exception as e:
		print('Exception: {}'.format(e))
		raise ValueError(__GETCONFIGIBM_ERROR__)
			
	return results
	
def getConfigCamera():
	results = {}
	
	dict = getConfig()
	try:
		dict = dict['Camera']
		results['stream_address'] = dict['stream_address']
		results['stream_rootcapath'] = dict['stream_rootcapath']
		results['stream_certificatepath'] = dict['stream_certificatepath']
		results['stream_privatekeypath'] = dict['stream_privatekeypath']
		results['stream_privatekeypassword'] = dict['stream_privatekeypassword']
	except Exception as e:
		print('Exception: {}'.format(e))
		raise ValueError(__GETCONFIGCAMERA_ERROR__)
			
	return results
	
def getConfigServer():
	results = {}
	
	dict = getConfig()
	try:
		dict = dict['Server']
		results['server_port'] = int(dict['server_port'])
		results['rootcapath'] = dict['rootcapath']
		results['certificatepath'] = dict['certificatepath']
		results['privatekeypath'] = dict['privatekeypath']
		results['privatekeypassword'] = dict['privatekeypassword']
	except Exception as e:
		print('Exception: {}'.format(e))
		raise ValueError(__GETCONFIGSERVER_ERROR__)
			
	return results
	
def doVisualRecognition(filename):
	results = {}
	
	if os.path.isfile(filename):
		apikey = getConfigIBM()['ibm_visualrecognition_apikey']
		with open(filename,'rb') as file:
			visual_recognition = VisualRecognitionV3('2016-05-20', api_key=apikey)
			results = visual_recognition.classify(images_file=file)
		
	return results
	
def deleteFile(filename):
	if os.path.isfile(filename):
		os.remove(filename)
	
def getFromStream(url):
	response = None
	
	__CAMERACONFIG__ = getConfigCamera()
	stream_address = __CAMERACONFIG__['stream_address']
	stream_rootcapath = __CAMERACONFIG__['stream_rootcapath']
	stream_certificatepath = __CAMERACONFIG__['stream_certificatepath']
	stream_privatekeypath = __CAMERACONFIG__['stream_privatekeypath']
	stream_privatekeypassword = __CAMERACONFIG__['stream_privatekeypassword']
	
	try:
		url = '{}/{}'.format(stream_address,url)
		
		context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
		context.verify_mode = ssl.CERT_REQUIRED
		context.load_cert_chain(stream_certificatepath,stream_privatekeypath,stream_privatekeypassword)
		context.load_verify_locations(stream_rootcapath)
		
		response = urllib2.urlopen(url, context=context)
	except:
		pass
		
	return response
	
def getStreamStatus():
	status = False
	
	response = getFromStream('status')
	if response:
		response = json.loads(response.read())
		if 'Status' in response:
			status = response['Status']
			
	return status
	
def getImage():
	image = None
	
	response = getFromStream('image')
	if response:
		image = response.read()
	
	return image
	
def datetimeToTimestamp(d):
	return calendar.timegm(d.timetuple())
	
def timestampToLocal(t):
	utc_timezone = tz.tzutc()
	local_timezone = tz.gettz('Asia/Singapore')
	
	timestamp = datetime.fromtimestamp(t)
	timestamp = timestamp.replace(tzinfo=utc_timezone).astimezone(local_timezone)
	
	return timestamp
	
def textToSpeech(message):
	result = None
	if message:
		ibm_config = getConfigIBM()
		username = ibm_config['ibm_texttospeech_username']
		password = ibm_config['ibm_texttospeech_password']
		
		text_to_speech = TextToSpeechV1(
			username=username,
			password=password,
			x_watson_learning_opt_out=True
		)
		
		try:
			result = text_to_speech.synthesize(message, accept='audio/wav', voice='en-US_AllisonVoice')
		except:
			pass
		
	return result
	
def hasKeys(dict,keys):
	bool = True
	
	for k in keys:
		if k not in dict:
			bool = False
			break
			
	return bool
	
def convertLight(value):
	return round((1024 / value) % 1024)
	
def createSensorTable():
	attributeDefinitions = [
		{
			'AttributeName': 'Room',
			'AttributeType': 'S',
		},
		{
			'AttributeName': 'Timestamp',
			'AttributeType': 'N',
		}
	]
	
	keySchema = [
		{
			'AttributeName': 'Room',
			'KeyType': 'HASH',
		},
		{
			'AttributeName': 'Timestamp',
			'KeyType': 'RANGE',
		}
	]
	
	createTable('Sensor',attributeDefinitions,keySchema)
	
def createSubscriptionTable():
	attributeDefinitions = [
		{
			'AttributeName': 'Topic',
			'AttributeType': 'S',
		}
	]
	
	keySchema = [
		{
			'AttributeName': 'Topic',
			'KeyType': 'HASH',
		}
	]
	
	createTable('Subscription',attributeDefinitions,keySchema)

def getSubscription(topic):
	condition = Key('Topic').eq(topic)
	subscription = query('Subscription',condition,limit=1)
	
	if subscription:
		subscription = subscription[0]
	
	return subscription