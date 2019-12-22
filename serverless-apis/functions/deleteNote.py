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

        dynamodb.call("delete_item")(
            Key={
                'userid': userid,
                'noteId': event['pathParameters']['noteId']
            }
        )
        # Return the matching list of items in response body
        return success({'status': True})
    except ClientError as e:
        return failure({'status': False})
