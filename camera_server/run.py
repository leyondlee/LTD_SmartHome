from PIL import Image
from tornado.httpserver import HTTPServer
from lib import getConfigServer, getConfigCamera
import tornado.ioloop
import tornado.web
import tornado
import urllib2
import json
import base64
import time
import io
import socket
import ssl
import struct
import threading
import select

__SERVERCONFIG__ = getConfigServer()
server_port = __SERVERCONFIG__['server_port']
main_host = __SERVERCONFIG__['main_host']
rootcapath = __SERVERCONFIG__['rootcapath']
certificatepath = __SERVERCONFIG__['certificatepath']
privatekeypath = __SERVERCONFIG__['privatekeypath']
privatekeypassword = __SERVERCONFIG__['privatekeypassword']

__CAMERACONFIG__ = getConfigCamera()
stream_port = __CAMERACONFIG__['stream_port']
stream_rootcapath = __CAMERACONFIG__['stream_rootcapath']
stream_certificatepath = __CAMERACONFIG__['stream_certificatepath']
stream_privatekeypath = __CAMERACONFIG__['stream_privatekeypath']
stream_privatekeypassword = __CAMERACONFIG__['stream_privatekeypassword']

class Camera(threading.Thread):
	_instance = None
	
	loop = True
	frame = None
	
	def __init__(self):
		threading.Thread.__init__(self)
	
	def __new__(self):
		if not self._instance:
			self._instance = super(Camera,self).__new__(self)
			
		return self._instance
		
	def get_frame(self):
		return self.frame
		
	def run(self):
		context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
		context.verify_mode = ssl.CERT_REQUIRED
		context.load_cert_chain(certificatepath,privatekeypath,privatekeypassword)
		context.load_verify_locations(rootcapath)
		
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		s.bind(('0.0.0.0', 9000))
		s.listen(5)
		
		client = None
		lastwrite = None
		
		while self.loop:
			input = [s]
			if client:
				input.append(client['socket'])
			else:
				client = {}
				lastwrite = None
			
			rlist, wlist, xlist = select.select(input,[],[],0)
			
			for r in rlist: #Loop through ready objects
				if r == s:
					if not client:
						newclient = s.accept()[0]
						
						connected = True
						try:
							newclient = context.wrap_socket(newclient, server_side=True)
						except Exception as e:
							newclient.close()
							connected = False
							
						if connected:
							newclient.settimeout(30)
							client['socket'] = newclient
							client['file'] = newclient.makefile('rb')
							print('Client connected')
				elif r == client['socket']:
					disconnect = True
					try:
						file = client['file']
						image_len = struct.unpack('<L', file.read(struct.calcsize('<L')))[0]
						if image_len:
							image_stream = io.BytesIO()
							image_stream.write(file.read(image_len))
							image_stream.seek(0)
							image = Image.open(image_stream)
							image.verify()
							self.frame = image_stream.getvalue()
							
							lastwrite = time.time()
							disconnect = False
					except socket.timeout:
						client['file'].close()
						client['socket'].close()
						print('Client timeout')
					except Exception as e:
						print(e)
						
					if disconnect:
						client = None
						self.frame = None
						print('Client disconnected')
		
			now = time.time()
			if client and lastwrite and (now - lastwrite) > 10:
				client['file'].close()
				client['socket'].close()
				client = None
				self.frame = None
				print('Client timeout')
		
		if client:
			client['file'].close()
			client['socket'].close()
		
		s.close()
			
	def stop(self):
		self.loop = False

def authenticate(requestHandler):
	authenticated = False
	if requestHandler.request.get_ssl_certificate():
		authenticated = True
	else:
		apikey = requestHandler.get_argument('apikey',None)
		if apikey:
			try:
				url = '{}/auth/status'.format(main_host)
				ctx = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
				apikey = base64.b64encode(apikey)
				headers = {
					'Authorization': 'Basic {}'.format(apikey)
				}
				req = urllib2.Request(url, headers=headers)
				response = urllib2.urlopen(req, context=ctx)
				data = json.load(response)
				authenticated = data['Authenticated']
			except:
				pass
	
	return authenticated

class StreamingHandler(tornado.web.RequestHandler):
	@tornado.web.asynchronous
	@tornado.gen.coroutine
	def get(self):
		if authenticate(self):
			camera = Camera()
			
			ioloop = tornado.ioloop.IOLoop.current()
			
			self.set_header('Cache-Control', 'no-store, no-cache, must-revalidate, pre-check=0, post-check=0, max-age=0')
			self.set_header('Connection', 'close')
			self.set_header('Content-Type', 'multipart/x-mixed-replace;boundary=--boundarydonotcross')
			self.set_header('Pragma', 'no-cache')
			
			my_boundary = "--boundarydonotcross\n"
			while True:
				frame = camera.frame
				if frame:
					self.write(my_boundary)
					self.write('Content-type: image/jpeg\r\n')
					self.write('Content-length: {}\r\n\r\n'.format(len(frame)))
					self.write(str(frame))
					yield tornado.gen.Task(self.flush)
				else:
					break
		else:
			self.set_status(401)
			self.write('Unauthorized')
				
		self.finish()
				
class ImageHandler(tornado.web.RequestHandler):
	@tornado.web.asynchronous
	def get(self):
		if authenticate(self):
			camera = Camera()
			frame = camera.frame
			if frame:
				self.set_header('Content-Type', 'image/jpeg')
				self.set_header('Content-length', len(frame))
				self.write(frame)
		else:
			self.set_status(401)
			self.write('Unauthorized')
				
		self.finish()
		
class StatusHandler(tornado.web.RequestHandler):
	def get(self):
		if authenticate(self):
			camera = Camera()
			frame = camera.frame
			
			status = False
			if frame:
				status = True
			
			self.write(json.dumps({'Status':status}))
		else:
			self.set_status(401)
			self.write('Unauthorized')
	
camera = Camera()
camera.start()

app = tornado.web.Application([
	(r'/', StreamingHandler),
	(r'/image', ImageHandler),
	(r'/status', StatusHandler)
])

if __name__ == "__main__":
	try:
		ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
		ssl_ctx.verify_mode = ssl.CERT_OPTIONAL
		ssl_ctx.load_cert_chain(certificatepath,privatekeypath,privatekeypassword)
		ssl_ctx.load_verify_locations(rootcapath)
		
		server = HTTPServer(app, ssl_options=ssl_ctx)
		server.listen(server_port)
		tornado.ioloop.IOLoop.current().start()
	except KeyboardInterrupt:
		camera.stop()
	except Exception as e:
		print(e)