import boto3
from functions.shared import dynamodb
from functions.shared.response import success, failure
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key
from functions_cognito.shared import dynamodb as cognito_dynamodb
from collections import Counter
from os import environ


def number_of_users_in_each_status_of_the_program():
    data = cognito_dynamodb.get_cached_table_scan(environ['cache_bucket'], environ['usersTableName'])
    return Counter([a.get('status', 'No Status') for a in data])


def number_of_users_per_doctor():
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(environ['usersTableName'])
    result = table.query(
        IndexName='this_is_a_physician-index',
        KeyConditionExpression=Key('this_is_a_physician').eq('X'))['Items']
    doc_id_to_name = {a['userid']: f"{a.get('first_name', '')} {a.get('last_name', '')}".strip() for a in result}
    # response = table.scan()
    data = cognito_dynamodb.get_cached_table_scan(environ['cache_bucket'], environ['usersTableName'])
    return Counter([doc_id_to_name.get(a.get('physicians_userid')) for a in data if 'physicians_userid' in a])


def main(event, context):
    try:
        cognitoPoolUserId = event['requestContext']['identity']['cognitoAuthenticationProvider'].split(':')[-1]
        userid = cognito_dynamodb.get_userid(cognitoPoolUserId)

        d = {'reports': [(1, 'Number of Users in Each Status of the Program'),
                         (2, 'Number of Users per Doctor')]}

        if event['pathParameters'] is not None and 'reportId' in event['pathParameters']:
            requested_report_id = int(event['pathParameters']['reportId'])

            if requested_report_id == 1:
                d['selectedReportData'] = number_of_users_in_each_status_of_the_program()
            if requested_report_id == 2:
                d['selectedReportData'] = number_of_users_per_doctor()

        return success(d)
    except ClientError as e:
        return failure({'status': False})
