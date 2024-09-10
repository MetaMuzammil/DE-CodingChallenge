import json
import os
import boto3
from datetime import datetime
from weather_au import api

def get_ssm_parameter(parameter_name):
    ssm = boto3.client('ssm')

    response = ssm.get_parameter(Name=parameter_name, WithDecryption=False)
    return response['Parameter']['Value'].split(',')


def lambda_handler(event, context):
    s3 = boto3.client('s3')
    lambda_client = boto3.client('lambda')

    raw_bucket = os.environ['RAW_BUCKET']
    partition_lambda_arn = os.environ['PARTITION_LAMBDA_ARN']

    locations = get_ssm_parameter('LocationList')

    for loc in locations:
        weather = api.WeatherApi(search=loc, debug=0)
        observations = weather.observations()
        forecast_json = json.dumps(observations)

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"weather_data_{loc}_{timestamp}.json"

        s3.put_object(
            Bucket=raw_bucket,
            Key=filename,
            Body=forecast_json
        )

        invoke_response = lambda_client.invoke(
            FunctionName=partition_lambda_arn,
            InvocationType='Event',
            Payload=json.dumps({
                'bucket': raw_bucket,
                'key': filename,
                'location': loc
            })
        )

    return {
        'statusCode': 200,
        'body': json.dumps('Weather data retrieved for all locations, stored in S3, and partition Lambda invoked.')
    }