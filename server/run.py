from gevent import monkey; monkey.patch_all()
from app import app
from gevent.pywsgi import WSGIServer
import ssl

try:
	ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
	ssl_ctx.load_cert_chain(app.config['CERTIFICATEPATH'],app.config['PRIVATEKEYPATH'],app.config['PRIVATEKEYPASSWORD'])
	ssl_ctx.load_verify_locations(app.config['ROOTCAPATH'])

	http_server = WSGIServer(('0.0.0.0',app.config['SERVER_PORT']),app,ssl_context=ssl_ctx)
	http_server.serve_forever()
except KeyboardInterrupt:
	pass
except Exception as e:
	print('Exception: {}'.format(e))