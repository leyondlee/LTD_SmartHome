from decimal import Decimal
import app
import json

class DecimalEncoder(json.JSONEncoder):
	def default(self, o):
		if isinstance(o, Decimal):
			if o % 1 > 0:
				return float(o)
			else:
				return int(o)
		return super(DecimalEncoder, self).default(o)
		
def createTable(tablename,attributeDefinitions,keySchema):
	dynamodb = app.dynamodb
	
	success = True
	try:
		dynamodb.create_table(
			AttributeDefinitions=attributeDefinitions,
			KeySchema=keySchema,
			TableName=tablename,
			ProvisionedThroughput={
				'ReadCapacityUnits': 5,
				'WriteCapacityUnits': 5,
			}
		)
	except:
		success = False
		
	return success
		
def deleteTable(tablename):
	dynamodb = app.dynamodb
	table = dynamodb.Table(tablename)
	
	success = True
	try:
		table.delete()
	except:
		success = False
		
	return success
	
def query(tablename,condition,columns=None,expressions=None,limit=None):
	dynamodb = app.dynamodb
	table = dynamodb.Table(tablename)
	
	args = {'KeyConditionExpression': condition}
	if columns:
		args['ProjectionExpression'] = columns
		
	if expressions:
		args['ExpressionAttributeNames'] = expressions
		
	if limit:
		args['Limit'] = limit
	
	results = None
	try:
		response = table.query(**args)
		results = response['Items']
		
		while 'LastEvaluatedKey' in response:
			args['ExclusiveStartKey'] = response['LastEvaluatedKey']
			response = table.query(**args)
			
			results.extend(response['Items'])
	except:
		pass
		
	return results
	
def scan(tablename):
	dynamodb = app.dynamodb
	table = dynamodb.Table(tablename)
	
	results = []
	try:
		response = table.scan()
		results = response['Items']
		
		while 'LastEvaluatedKey' in response:
			response = table.scan({ExclusiveStartKey: response['LastEvaluatedKey']})
			
			results.extend(response['Items'])
	except:
		pass
		
	return results
	
def safeValues(dict):
	for k, v in dict.iteritems():
		if isinstance(v, float):
			dict[k] = Decimal(v)
			
	return dict
	
def putItem(tablename,item):
	dynamodb = app.dynamodb
	table = dynamodb.Table(tablename)
			
	item = safeValues(item)
	
	success = True
	try:
		table.put_item(
			Item=item
		)
	except:
		success = False
		
	return success
		
def deleteItem(tablename,key):
	dynamodb = app.dynamodb
	table = dynamodb.Table(tablename)
	
	key = safeValues(key)
	
	success = True
	try:
		table.delete_item(
			Key=key
		)
	except:
		success = False
		
	return success
	
def updateItem(tablename,key,updateExpression,expressionAttributeValues):
	dynamodb = app.dynamodb
	table = dynamodb.Table(tablename)
	
	success = True
	try:
		table.update_item(
			Key=key,
			UpdateExpression=updateExpression,
			ExpressionAttributeValues=expressionAttributeValues
		)
	except:
		success = False
		
	return success