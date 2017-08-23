import ConfigParser

__GETCONFIGCAMERA_ERROR__ = '''
[Camera]
Missing field(s) or wrong type.
Fields must be as follows:
	> stream_host - STRING
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
	
def getConfigCamera():
	results = {}
	
	dict = getConfig()
	try:
		dict = dict['Camera']
		results['stream_host'] = dict['stream_host']
		results['stream_port'] = int(dict['stream_port'])
		results['stream_rootcapath'] = dict['stream_rootcapath']
		results['stream_certificatepath'] = dict['stream_certificatepath']
		results['stream_privatekeypath'] = dict['stream_privatekeypath']
		results['stream_privatekeypassword'] = dict['stream_privatekeypassword']
	except Exception as e:
		print('Exception: {}'.format(e))
		raise ValueError(__GETCONFIGCAMERA_ERROR__)
			
	return results