from app.mod_auth.models import User
from app.dynamodblib import deleteTable
import getpass
import app
import os

while True:
	input = raw_input('''Please select an option:
(1) Create User
(2) Delete User
(3) List Users
(4) Delete Sensor Table
(5) Delete Subscription Table
(q) Exit
--> ''')

	if input == '1':
		username = raw_input('''- Create User -
Username (Enter \'q\' to quit): ''')
		
		if username != 'q':
			user = User.query.get(username)
			if not user:
				password = getpass.getpass('Password: ')
				confirmpassword = getpass.getpass('Confirm Password: ')
				
				if password == confirmpassword:
					user = User(username)
					user.set_password(password)
					user.add()
					
					print('User "{}" created'.format(username))
				else:
					print('Error: Passwords do not match'.format(username))
			else:
				print('Error: User "{}" already exist'.format(username))
				
		print('-------------------------------------')
	elif input == '2':
		username = raw_input('''- Delete User -
Username (Enter \'q\' to quit): ''')
		
		if username != 'q':
			user = User.query.get(username)
			if user:
				user.delete()
				
				print('User "{}" deleted'.format(username))
			else:
				print('Error: User "{}" does not exist'.format(username))
				
		print('-------------------------------------')
	elif input == '3':
		print('- List Users -')
		
		users = User.query.all()
		if users:
			for user in users:
				print(user.username)
		else:
			print('There are no users')
			
		print('-------------------------------------')
	elif input == '4':
		deleteTable('Sensor')
		print('Sensor table deleted')
		print('-------------------------------------')
	elif input == '5':
		deleteTable('Subscription')
		print('Subscription table deleted')
		print('-------------------------------------')
	elif input == 'q':
		break
		
os._exit(0)