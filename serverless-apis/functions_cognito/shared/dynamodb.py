import boto3
import os
from boto3.dynamodb.conditions import Key, Attr
import json


def get_cached_table_scan(cache_bucket, table_name):
    s3_resource = boto3.resource('s3')
    obj = s3_resource.Object(cache_bucket, table_name+'.json')
    return json.loads(obj.get()['Body'].read())


def call(action):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['usersTableName'])
    return getattr(table, action)


def get_user_attributes_from_userid(userid):
    return call("get_item")(
        Key={
            'userid': userid
        }
    )


def get_userid(cognito_user_id):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['usersTableName'])

    data = table.query(
        IndexName='cognito_user_id-index',
        KeyConditionExpression=Key('cognito_user_id').eq(cognito_user_id),
        Select='SPECIFIC_ATTRIBUTES',
        ProjectionExpression='userid'
    )
    return data['Items'][0]['userid']


def get_user_attributes_from_cognito_id(cognito_user_id):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['usersTableName'])

    data = table.query(
        IndexName='cognito_user_id-index',
        KeyConditionExpression=Key('cognito_user_id').eq(cognito_user_id)
    )
    return data['Items'][0]


def get_users_from_email(email):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['usersTableName'])

    data = table.query(
        IndexName='email-index',
        KeyConditionExpression=Key('email').eq(email)
    )
    return data['Items']


def get_physicians():
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['usersTableName'])

    data = table.query(
        IndexName='this_is_a_physician-index',
        KeyConditionExpression=Key('this_is_a_physician').eq('X')
    )
    return data['Items']
