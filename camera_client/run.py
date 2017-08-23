from lib import getConfigCamera
from signal import pause
from time import sleep
import io
import socket
import ssl
import struct
import picamera
import select

__CAMERACONFIG__ = getConfigCamera()
stream_host = __CAMERACONFIG__['stream_host']
stream_port = __CAMERACONFIG__['stream_port']
stream_rootcapath = __CAMERACONFIG__['stream_rootcapath']
stream_certificatepath = __CAMERACONFIG__['stream_certificatepath']
stream_privatekeypath = __CAMERACONFIG__['stream_privatekeypath']
stream_privatekeypassword = __CAMERACONFIG__['stream_privatekeypassword']

class SplitFrames(object):
	def __init__(self, connection):
		self.connection = connection
		self.stream = io.BytesIO()

	def write(self, buf):
		if buf.startswith(b'\xff\xd8'):
			# Start of new frame; send the old one's length
			# then the data
			size = self.stream.tell()
			if size > 0:
				self.connection.write(struct.pack('<L', size))
				self.connection.flush()
				self.stream.seek(0)
				self.connection.write(self.stream.read(size))
				self.stream.seek(0)
			
		self.stream.write(buf)

context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
context.verify_mode = ssl.CERT_REQUIRED
context.load_cert_chain(stream_certificatepath,stream_privatekeypath,stream_privatekeypassword)
context.load_verify_locations(stream_rootcapath)

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ssl_sock = context.wrap_socket(s)

try:
	ssl_sock.connect((stream_host, stream_port))
	ssl_sock.settimeout(30)
	connection = ssl_sock.makefile('wb')

	print('Connected to server')
	output = SplitFrames(connection)
	with picamera.PiCamera(resolution='VGA', framerate=30) as camera:
		camera.start_recording(output, format='mjpeg')
		
		connected = True
		while connected:
			try:
				input = [connection]
				
				rlist, wlist, xlist = select.select(input,[],[],0)
				
				for r in rlist:
					if r == connection:
						try:
							data = r.read()
							if not data:
								connected = False
						except Exception as e:
							connected = False
							print('Exception: {}'.format(e))
			except KeyboardInterrupt:
				connected = False
		
		camera.stop_recording()
		
		if connected:
			connection.write(struct.pack('<L', 0))
		else:
			print('Disconnected from server')
			
	connection.close()
	ssl_sock.close()
except Exception as e:
	print('Exception: {}'.format(e))