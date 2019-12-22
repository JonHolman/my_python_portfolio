import boto3
import os


def call(action):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['notesTableName'])

    return getattr(table, action)
