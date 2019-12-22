from functions.shared import dynamodb
from functions.shared.response import success, failure
from botocore.exceptions import ClientError
from functions_cognito.shared import dynamodb as cognito_dynamodb


def main(event, context):
    try:
        if event['pathParameters'] is None or 'userid' not in event['pathParameters']:
            cognitoPoolUserId = event['requestContext']['identity']['cognitoAuthenticationProvider'].split(
                ':')[-1]
            userid = cognito_dynamodb.get_userid(cognitoPoolUserId)
        else:
            userid = event['pathParameters']['userid']

        result = dynamodb.call("get_item")(
            Key={
                'userid': userid,
                'noteId': event['pathParameters']['noteId']
            }
        )

        if result['Item']:
            # Return the retrieved item
            return success(result['Item'])
        else:
            return failure({'status': False, 'error': "Item not found."})
    except ClientError as e:
        return failure({'status': False})
