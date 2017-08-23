from app.common import getConfigServer, getConfigDatabase
import uuid

DEBUG = True

__SERVERCONFIG__ = getConfigServer()
SERVER_PORT = __SERVERCONFIG__['server_port']
ROOTCAPATH = __SERVERCONFIG__['rootcapath']
CERTIFICATEPATH = __SERVERCONFIG__['certificatepath']
PRIVATEKEYPATH = __SERVERCONFIG__['privatekeypath']
PRIVATEKEYPASSWORD = __SERVERCONFIG__['privatekeypassword']

__DBCONFIG__ = getConfigDatabase()
DB_HOST = __DBCONFIG__['db_host']
DB_PORT = __DBCONFIG__['db_port']
DB_USERNAME = __DBCONFIG__['db_user']
DB_PASSWORD = __DBCONFIG__['db_password']
DB_DATABASE = __DBCONFIG__['db_database']

SQLALCHEMY_DATABASE_URI = 'mysql://{}:{}@{}:{}/{}'.format(DB_USERNAME,DB_PASSWORD,DB_HOST,DB_PORT,DB_DATABASE)
DATABASE_CONNECT_OPTIONS = {}

SQLALCHEMY_TRACK_MODIFICATIONS = False

SECRET_KEY = str(uuid.uuid4())