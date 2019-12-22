#!/usr/bin/env python
# simple script to copy items from one dynamodb table to another.
import boto3

source_table = input('Enter the name of the source table: ')
destination_table = input('Enter the name of the destination table: ')

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

source_table = dynamodb.Table(source_table)
response = source_table.scan()
data = response['Items']

while response.get('LastEvaluatedKey', False):
    response = source_table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
    data.extend(response['Items'])

print(f'{len(data)} total items to copy.')

input('Press enter to continue')

destination_table = dynamodb.Table(destination_table)

for i, d in enumerate(data):
    print(i+1, end='\r', flush=True)
    if 'userid' in d:
        d['userid'] = d.pop('userid')
    destination_table.put_item(Item=d)
