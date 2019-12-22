import boto3
from functions_cognito.shared.response import success, failure
from os import environ
import json
import decimal
from datetime import datetime
from dateutil.tz import tzutc
from functions_cognito.shared import dynamodb as cognito_dynamodb


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)


def modified_over_an_hour_ago():
    try:
        s3client = boto3.client('s3')
        head = s3client.head_object(Bucket=environ['cache_bucket'], Key=environ['usersTableName']+'.json')
        return (datetime.now(tzutc()) - head['LastModified']).seconds/60/60 > 1
    except Exception as e:
        return True


def main(event, context):
    ssm_client = boto3.client('ssm')
    if bool(int(ssm_client.get_parameter(Name=environ['exportUsersJson_param'])['Parameter']['Value'])) and modified_over_an_hour_ago():
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.Table(environ['usersTableName'])

        response = table.scan()
        data = response['Items']
        while response.get('LastEvaluatedKey', False):
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            data.extend(response['Items'])

        providers = cognito_dynamodb.get_physicians()
        providers = {a['userid']: f"{a.get('first_name', '')} {a.get('last_name', '')}".strip()
                     for a in providers}

        for d in data:
            if 'physicians_userid' in d:
                d['provider'] = providers.get(d['physicians_userid'], 'Unknown')

        # fields removed from fields_we_want:
        # 'total_scholarship_amount', 'participant_payment_amount', 'invoice'
        fields_we_want = ['insurance_member_num', 'cognito_user_id', 'phone_number', 'class_start_date', 'state', 'userid', 'city',
                          'baycare_scholarship_id', 'zip', 'gender', 'first_name', 'date_of_referral', 'class_location', 'email', 'group',
                          'status', 'referral_type', 'dob', 'this_is_a_physician', 'last_name', 'address', 'provider', 'physicians_userid']
        data = [{k: v for k, v in a.items() if k in fields_we_want} for a in data]

        s3client = boto3.client('s3')
        s3client.put_object(Bucket=environ['cache_bucket'], Key=environ['usersTableName'] +
                            '.json', Body=json.dumps(data, cls=DecimalEncoder))

        # fields_we_want = ['first_name', 'last_name', 'userid']
        # data = [{k: v for k, v in a.items() if k in fields_we_want} for a in data]

        # s3client.put_object(Bucket=environ['cache_bucket'], Key=environ['usersTableName'] +
        #                     'FLIDonly.json', Body=json.dumps(data, cls=DecimalEncoder))

        # setting the parameter to '0' (false) so that it will not run again until createUser.py sets it to '1' again
        ssm_client.put_parameter(Name=environ['exportUsersJson_param'], Value='0', Type='String', Overwrite=True)
