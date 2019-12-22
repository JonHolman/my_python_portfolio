from functions.shared import dynamodb
from functions.shared.response import success, failure
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key
from functions_cognito.shared import dynamodb as cognito_dynamodb


def main(event, context):
    try:
        result = cognito_dynamodb.get_physicians()
        result = [
            [a['userid'], f"{a.get('first_name', '')} {a.get('last_name', '')}".strip()] for a in result]
        return success(result)
    except ClientError as e:
        return failure({'status': False})
