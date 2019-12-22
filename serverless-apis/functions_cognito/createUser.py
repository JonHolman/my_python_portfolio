import boto3
import uuid
import json
from functions_cognito.shared import dynamodb
from functions_cognito.shared.response import success, failure
from botocore.exceptions import ClientError
from os import environ
from decimal import Decimal
import string
import secrets
import re


def valid_password(password):
    flag = 0
    while True:
        if len(password) < 8:
            flag = -1
            break
        elif not re.search("[a-z]", password):
            flag = -1
            break
        elif not re.search("[A-Z]", password):
            flag = -1
            break
        elif not re.search("[0-9]", password):
            flag = -1
            break
        elif not re.search("[!#$%&'()*+,-./:;<=>?@[\\]^_`{|}~]", password):
            flag = -1
            break
        elif re.search(r"\s", password):
            flag = -1
            break
        else:
            return True
    if flag == -1:
        return False


def generate_password():
    good_password = False
    while not good_password:
        alphabet = (
            string.ascii_letters + string.digits +
            "!#$%&'()*+,-./:;<=>?@[\\]^_`{|}~"
        )
        password = "".join(secrets.choice(alphabet) for i in range(16))
        good_password = valid_password(password)
    return password


def get_cognito_groups(client, user_pool_id, cognito_username):
    groups = client.admin_list_groups_for_user(
        UserPoolId=user_pool_id,
        Username=cognito_username
    )
    groups = [a['GroupName'] for a in groups['Groups']]
    return groups


def create_cognito_user(cognito_client, user_pool_id, email):
    password = generate_password()

    response = cognito_client.admin_create_user(
        UserPoolId=user_pool_id,
        Username=email,
        UserAttributes=[{"Name": "email", "Value": email}],
        DesiredDeliveryMediums=["EMAIL"],
        TemporaryPassword=password,
    )

    cognito_client.admin_set_user_password(
        UserPoolId=user_pool_id, Username=email, Password=password, Permanent=True
    )

    return response


def main(event, context):
    try:
        client = boto3.client("cognito-idp")
        user_pool_id = environ["user_pool_id"]
        is_admin = False

        if 'requestContext' in event:
            cognitoAuthenticationProvider = event["requestContext"]["identity"]["cognitoAuthenticationProvider"]
            if cognitoAuthenticationProvider is not None:
                requester_cognitoUserId = cognitoAuthenticationProvider.split(
                    ":")[-1]
                is_admin = ('Admin' in get_cognito_groups(
                    client, user_pool_id, requester_cognitoUserId))

        body = json.loads(event["body"], parse_float=Decimal)
        data = body["attributes"]

        if 'cognito_user_id' not in data and 'email' in data and len(data['email']) > 2 and len(dynamodb.get_users_from_email(data['email'])) > 0:
            return failure({'status': False, 'message': 'An account with the given email already exists.'})
        elif ('requestContext' in event and not is_admin and (cognitoAuthenticationProvider is not None and requester_cognitoUserId != data['cognito_user_id'])):
            return failure({'status': False, 'message': 'Unauthorized.'})

        if 'requestContext' not in event or 'cognito_user_id' in data:
            user = client.admin_get_user(
                UserPoolId=user_pool_id, Username=data["email"])
            # user variable {'Username': 'uuid', 'UserAttributes': [{'Name': 'sub', 'Value': ''}, {'Name': 'email', 'Value': 'email@email'}]
        elif 'requestContext' in event and data.get('create_login', False):
            user = create_cognito_user(client, user_pool_id, data["email"])
            data["cognito_user_id"] = user["User"]["Username"]
            # user variable {'User': {'Username': 'uuid', 'Attributes': [{'Name': 'sub', 'Value': ''}, {'Name': 'email', 'Value': 'email@email'}]

        # Make admin functionality in lambda
        if 'requestContext' in event:
            if data.get('create_login', False):
                if is_admin:
                    if data['admin']:
                        client.admin_add_user_to_group(
                            UserPoolId=user_pool_id,
                            Username=data["email"],
                            GroupName='Admin'
                        )
                    else:
                        client.admin_remove_user_from_group(
                            UserPoolId=user_pool_id,
                            Username=data["email"],
                            GroupName='Admin'
                        )
                if data.get('this_is_a_physician', False):
                    client.admin_add_user_to_group(
                        UserPoolId=user_pool_id,
                        Username=data["email"],
                        GroupName='Physicians'
                    )
                else:
                    client.admin_remove_user_from_group(
                        UserPoolId=user_pool_id,
                        Username=data["email"],
                        GroupName='Physicians'
                    )
            else:
                if not data.get('create_login', False) and 'cognito_user_id' in data:
                    client.admin_delete_user(
                        UserPoolId=user_pool_id,
                        Username=data["email"]
                    )
                    data['cognito_user_id'] = ''

        if data.pop('this_is_a_physician', False):
            data['this_is_a_physician'] = 'X'

        # validate that the user being submitted matches a user that exists in the cognito user db (if they have a login)
        if (
            'requestContext' in event
            or "email" not in data
            or user["Username"] == data["cognito_user_id"]
        ):
            item = {k: v for k, v in data.items() if v != "" and k not in [
                'admin', 'create_login']}
            if 'userid' not in item:
                item['userid'] = str(uuid.uuid1())

            dynamodb.call("put_item")(Item=item)

            if ('requestContext' not in event or data.get('create_login', False)) and "email" in data:
                client.admin_update_user_attributes(
                    UserPoolId=user_pool_id,
                    Username=data["email"],
                    UserAttributes=[
                        {"Name": "custom:userid", "Value": item["userid"]}
                    ],
                )

            # setting the parameter to '1' (true) so that userTableToJson knows to run
            ssm_client = boto3.client('ssm')
            ssm_client.put_parameter(Name=environ['exportUsersJson_param'], Value='1', Type='String', Overwrite=True)

            return success({"userid": item["userid"]})
        else:
            return failure({"status": False})
    except ClientError as e:
        return failure({'status': False})
