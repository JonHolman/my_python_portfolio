#!/usr/bin/env python3
from pprint import pprint
import subprocess

bashCommand = "./get_config_values.sh"
process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
output, error = process.communicate()

if error:
    print('ERROR:', error)
else:
    deployment_values = dict(
        [a.split(': ') for a in output.decode("utf-8").split('\n') if a != ''])

    d = {
        'REGION': "us-east-1",
        'MAX_ATTACHMENT_SIZE': 5*1024*1024,
        's3': {
            'BUCKET': deployment_values['AttachmentsBucketName']
        },
        'apiGateway': {
            'URL': deployment_values['ServiceEndpoint']
        },
        'cognito': {
            'USER_POOL_ID': deployment_values['UserPoolId'],
            'APP_CLIENT_ID': deployment_values['UserPoolClientId'],
            'IDENTITY_POOL_ID': deployment_values['IdentityPoolId']
        }
    }

    pprint(d)
