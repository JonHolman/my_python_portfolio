import boto3
from functions_cognito.shared.response import success, failure
from os import environ
from functions_cognito.shared import dynamodb as cognito_dynamodb
import decimal


def main(event, context):
    try:
        if event['pathParameters'] is None or 'userid' not in event['pathParameters']:
            cognitoPoolUserId = event['requestContext']['identity']['cognitoAuthenticationProvider'].split(
                ':')[-1]
            userid = cognito_dynamodb.get_userid(cognitoPoolUserId)
        else:
            userid = event['pathParameters']['userid']

        user = cognito_dynamodb.get_user_attributes_from_userid(userid)

        if 'cognito_user_id' in user['Item'] and len(user['Item']['cognito_user_id'].strip()) > 0:
            user_pool_id = environ['user_pool_id']
            client = boto3.client('cognito-idp')
            groups = client.admin_list_groups_for_user(
                UserPoolId=user_pool_id,
                Username=user['Item']['cognito_user_id']
            )
        else:
            groups = {'Groups': []}

        for i in user['Item']:
            if isinstance(user['Item'][i], decimal.Decimal):
                user['Item'][i] = float(user['Item'][i])

        if 'this_is_a_physician' in user['Item'] and user['Item']['this_is_a_physician'] == 'X':
            user['Item']['this_is_a_physician'] = True

        # move user into a dictionary with username being the key, and add a groups list
        user = {'groups': [a['GroupName']
                           for a in groups['Groups']], 'UserAttributes': user['Item']}

        # Adding provider field, removing it from the client side
        if 'physicians_userid' in user['UserAttributes']:
            doc = cognito_dynamodb.get_user_attributes_from_userid(
                user['UserAttributes']['physicians_userid']).get('Item', {})
            user['UserAttributes']['provider'] = f"{doc.get('first_name', 'Unknown')} {doc.get('last_name', '')}".strip(
            )

        return success(user)
    except Exception as e:
        return failure({'status': False})
