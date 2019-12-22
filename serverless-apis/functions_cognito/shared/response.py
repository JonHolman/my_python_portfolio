import json
import decimal
import datetime


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return float(o)
        return super(DecimalEncoder, self).default(o)


def myconverter(o):
    if isinstance(o, datetime.datetime):
        return o.__str__()


def buildResponse(statusCode, body):
    return {
        'statusCode': statusCode,
        'headers': {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": True
        },
        'body': json.dumps(body, cls=DecimalEncoder, default=myconverter)
    }


def success(body):
    return buildResponse(200, body)


def failure(body):
    return buildResponse(500, body)
