import boto3
from functions_cognito.shared.response import success, failure
from os import environ
from functions_cognito.shared import dynamodb as cognito_dynamodb
import json
import urllib.parse
import math


def get_requestor_groups(client, user_pool_id, requesting_username):
    groups = client.admin_list_groups_for_user(
        UserPoolId=user_pool_id,
        Username=requesting_username
    )
    groups = [a['GroupName'] for a in groups['Groups']]
    return groups


def prep_attributes(i):
    if 'this_is_a_physician' in i and i['this_is_a_physician'] == 'X':
        i['this_is_a_physician'] = True
    return i


def main(event, context):
    try:
        pages = 1
        user_pool_id = environ['user_pool_id']
        cognitoPoolUserId = event['requestContext']['identity']['cognitoAuthenticationProvider'].split(':')[-1]

        client = boto3.client('cognito-idp')
        requestors_groups = get_requestor_groups(client, user_pool_id, cognitoPoolUserId)
        all_groups = client.list_groups(UserPoolId=user_pool_id)['Groups']

        data = cognito_dynamodb.get_cached_table_scan(environ['cache_bucket'], environ['usersTableName'])

        if event['pathParameters'] is not None and 'filter' in event['pathParameters']:
            filter = urllib.parse.unquote_plus(event['pathParameters']['filter']).lower()
            data = [d for d in data if filter in json.dumps(d).replace('"', '').replace('_', ' ').lower()]

        if 'Physicians' not in requestors_groups:
            if len(data) > 100:
                pages = math.ceil(len(data)/100)
            if event['pathParameters'] is not None and 'page' in event['pathParameters']:
                page = int(event['pathParameters']['page'])
                data = data[(page*100):((page*100)+100)]
            else:
                data = data[:100]

        all_users = {i['userid']: {'groups': [], 'Attributes': prep_attributes(i)} for i in data}

        for group in all_groups:
            group_response = client.list_users_in_group(
                UserPoolId=user_pool_id, GroupName=group['GroupName'])['Users']
            for g in group_response:
                if cognito_dynamodb.get_userid(g['Username']) in all_users:
                    all_users[cognito_dynamodb.get_userid(g['Username'])]['groups'].append(group['GroupName'])

        if 'Admin' in requestors_groups:
            d = {'users': [a[1] for a in list(all_users.items())], 'groups': all_groups, 'pages': pages}
            return success(d)
        elif 'Physicians' in requestors_groups:
            requestor_userid = cognito_dynamodb.get_userid(cognitoPoolUserId)
            return success({'users': [a[1] for a in list(all_users.items()) if a[1]['Attributes'].get('physicians_userid') == requestor_userid], 'groups': all_groups})
        else:
            return failure({'status': False})
    except Exception as e:
        return failure({'status': False})
