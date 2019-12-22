import uuid
import json
from time import time
from functions.shared import dynamodb
from functions.shared.response import success, failure
from botocore.exceptions import ClientError
import decimal
from functions_cognito.shared import dynamodb as cognito_dynamodb


def main(event, context):
    try:
        data = json.loads(event['body'].replace('\n', '\\n'))
        if event['pathParameters'] is None or 'userid' not in event['pathParameters']:
            cognitoPoolUserId = event['requestContext']['identity']['cognitoAuthenticationProvider'].split(
                ':')[-1]
            userid = cognito_dynamodb.get_userid(cognitoPoolUserId)
        else:
            userid = event['pathParameters']['userid']

        item = {
            'userid': userid,
            'authorId': cognito_dynamodb.get_userid(event['requestContext']['identity']['cognitoAuthenticationProvider'].split(':')[-1]),
            'noteId': str(uuid.uuid1()),
            'content': data['content'],
            'attachment': data['attachment'],
            'createdAt': int(round(time() * 1000))
        }
        result = dynamodb.call("put_item")(Item=item)
        # Return the matching list of items in response body
        return success(item)
    except ClientError as e:
        print('ClientError Exception:', e)
        print('event', event)
        return failure({'status': False})
    except Exception as e:
        print('Exception:', e)
        print('event', event)
        return failure({'status': False})
