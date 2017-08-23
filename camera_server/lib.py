import ConfigParser

__GETCONFIGSERVER_ERROR__ = '''
[Server]
Missing field(s) or wrong type.
Fields must be as follows:
	> server_port - INTEGER
	> main_host - STRING
	> rootcapath - STRING
	> certificatepath - STRING
	> privatekeypath - STRING
	> privatekeypassword - STRING
'''

__GETCONFIGCAMERA_ERROR__ = '''
[Camera]
Missing field(s) or wrong type.
Fields must be as follows:
	> stream_port - INTEGER
	> stream_rootcapath - STRING
	> stream_certificatepath - STRING
	> stream_privatekeypath - STRING
	> stream_privatekeypassword - STRING
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
	
def getConfigServer():
	results = {}
	
	dict = getConfig()
	try:
		dict = dict['Server']
		results['server_port'] = int(dict['server_port'])
		results['main_host'] = dict['main_host']
		results['rootcapath'] = dict['rootcapath']
		results['certificatepath'] = dict['certificatepath']
		results['privatekeypath'] = dict['privatekeypath']
		results['privatekeypassword'] = dict['privatekeypassword']
	except Exception as e:
		print('Exception: {}'.format(e))
		raise ValueError(__GETCONFIGSERVER_ERROR__)
			
	return results
	
def getConfigCamera():
	results = {}
	
	dict = getConfig()
	try:
		dict = dict['Camera']
		results['stream_port'] = int(dict['stream_port'])
		results['stream_rootcapath'] = dict['stream_rootcapath']
		results['stream_certificatepath'] = dict['stream_certificatepath']
		results['stream_privatekeypath'] = dict['stream_privatekeypath']
		results['stream_privatekeypassword'] = dict['stream_privatekeypassword']
	except Exception as e:
		print('Exception: {}'.format(e))
		raise ValueError(__GETCONFIGCAMERA_ERROR__)
			
	return results