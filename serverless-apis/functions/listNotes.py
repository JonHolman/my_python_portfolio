from functions.shared import dynamodb
from functions.shared.response import success, failure
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key
from functions_cognito.shared import dynamodb as cognito_dynamodb


def main(event, context):
    try:
        if event['pathParameters'] is None or 'userid' not in event['pathParameters']:
            cognitoPoolUserId = event['requestContext']['identity']['cognitoAuthenticationProvider'].split(
                ':')[-1]
            userid = cognito_dynamodb.get_userid(cognitoPoolUserId)
        else:
            userid = event['pathParameters']['userid']

        result = dynamodb.call("query")(
            KeyConditionExpression=Key('userid').eq(userid))

        for i in result['Items']:
            if 'authorId' in i:
                user = cognito_dynamodb.get_user_attributes_from_userid(i['authorId']).get('Item', {})
                i['author'] = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
            if 'last_modified_by' in i:
                user = cognito_dynamodb.get_user_attributes_from_userid(i['last_modified_by']).get('Item', {})
                i['last_modified_by'] = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()

        # Return the matching list of items in response body
        return success(result['Items'])
    except ClientError as e:
        return failure({'status': False})
