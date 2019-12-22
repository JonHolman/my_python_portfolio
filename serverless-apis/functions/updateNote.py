from functions.shared import dynamodb
from functions.shared.response import success, failure
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key
import json
from functions_cognito.shared import dynamodb as cognito_dynamodb


def main(event, context):
    try:
        data = json.loads(event['body'])
        if event['pathParameters'] is None or 'userid' not in event['pathParameters']:
            cognitoPoolUserId = event['requestContext']['identity']['cognitoAuthenticationProvider'].split(
                ':')[-1]
            userid = cognito_dynamodb.get_userid(cognitoPoolUserId)
        else:
            userid = event['pathParameters']['userid']

        if data.get('attachment', None) == '':
            data['attachment'] = None

        dynamodb.call("update_item")(
            Key={
                'userid': userid,
                'noteId': event['pathParameters']['noteId']
            },
            UpdateExpression="SET content = :content, attachment = :attachment, last_modified_by = :last_modified_by",
            ExpressionAttributeValues={
                ':attachment': data.get('attachment', None),
                ':content': data.get('content', None),
                ':last_modified_by': cognito_dynamodb.get_userid(event['requestContext']['identity']['cognitoAuthenticationProvider'].split(':')[-1])
            },
            ReturnValues="ALL_NEW"
        )
        # Return the matching list of items in response body
        return success({'status': True})
    except ClientError as e:
        return failure({'status': False})
