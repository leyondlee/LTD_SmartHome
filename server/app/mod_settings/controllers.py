from flask import Blueprint, render_template, request, redirect, url_for
from app.mod_settings.forms import AddRoomForm
from app.common import getSubscription
from app.dynamodblib import DecimalEncoder, query, scan, putItem, deleteItem, updateItem
from app.mqttlib import roomSubscribe, roomUnsubscribe
from boto3.dynamodb.conditions import Key
from decimal import Decimal
import app
import json
import time

mod_settings = Blueprint('settings', __name__, url_prefix='/settings')

@mod_settings.route('/', defaults={'action': None})
@mod_settings.route('/<action>', methods=['GET', 'POST'])
def configuration(action):
	form = AddRoomForm(request.form)
	
	error = None
	success = None
	
	if form.validate_on_submit():
		if action == 'add':
			topic = request.form['topic']
			displayname = request.form['displayname']
			nightlevel = request.form['nightlevel']
			
			subscription = getSubscription(topic)
			if subscription:
				error = 'Topic already exist.'
			else:
				item = {
					'Topic': topic,
					'Timestamp': time.time(),
					'Displayname': displayname,
					'Nightlevel': Decimal(nightlevel)
				}
				r = putItem('Subscription',item)
				if r:
					roomSubscribe(topic)
					success = 'Added new room.'
				else:
					error = 'Unable to add subscription.'
		elif action == 'edit':
			topic = request.form['topic']
			displayname = request.form['displayname']
			nightlevel = request.form['nightlevel']
			
			subscription = getSubscription(topic)
			if subscription:
				key = {
					'Topic': topic
				}
				updateExpression = 'set Displayname = :d, Nightlevel=:n'
				expressionAttributeValues = {
					':d': displayname,
					':n': Decimal(nightlevel)
				}
				r = updateItem('Subscription',key,updateExpression,expressionAttributeValues)
				if r:
					success = 'Room edited.'
				else:
					error = 'Unable to edit subscription.'
			else:
				error = 'Topic does not exist.'
			
	templateData = {
		'form': form,
		'error': error,
		'success': success
	}
	
	return render_template('settings/configuration.html', **templateData)
	
@mod_settings.route('/subscription/delete', defaults={'topic': None})
@mod_settings.route('/subscription/delete/<topic>')
def deletesubscription(topic):
	if topic:
		subscription = getSubscription(topic)
		
		if subscription:
			topic = subscription['Topic']
			key = {
				'Topic': topic
			}
			r = deleteItem('Subscription',key)
			if r:
				roomUnsubscribe(topic)
				condition = Key('Room').eq(topic)
				columns = '#timestamp'
				expressions = {'#timestamp':'Timestamp'}
				results = query('Sensor',condition,columns,expressions)
				for r in results:
					key = {
						'Room': topic,
						'Timestamp': r['Timestamp']
					}
					deleteItem('Sensor',key)
		
	return redirect(url_for('settings.configuration'))
	
@mod_settings.route('/subscription/json', defaults={'room': None})
@mod_settings.route('/subscription/json/<room>')
def subscriptionjson(room):
	if room:
		results = [getSubscription(room)]
	else:
		results = scan('Subscription')
	
	data = []
	
	if results:
		for s in results:
			data.append({
				'Topic': s['Topic'],
				'Timestamp': s['Timestamp'],
				'Displayname': s['Displayname'],
				'Nightlevel': s['Nightlevel']
			})
		
	return json.dumps(data, cls=DecimalEncoder)