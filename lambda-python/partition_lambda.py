import os
import json
import boto3
from datetime import datetime
import re

def extract_date_from_filename(filename):

    match = re.search(r'_(\d{14})\.json$', filename)
    if match:
        timestamp_str = match.group(1)
        date = datetime.strptime(timestamp_str, "%Y%m%d%H%M%S")
        return str(date)
    else:
        raise ValueError("Timestamp not found in the filename")

def lambda_handler(event, context):
    s3 = boto3.client('s3')
    glue = boto3.client('glue')

    processed_bucket = os.environ['PROCESSED_BUCKET']
    RoleArn = os.environ['GLUE_ROLE_ARN']
    databaseName = os.environ['ATHENA_DATABASE']

    raw_bucket = event['bucket']
    key = event['key']
    location = event['location']

    s3_path = f"s3://{processed_bucket}/{location}"

    crawler_name = f'{location}_crawler_dev'

    file_content = s3.get_object(Bucket=raw_bucket, Key=key)['Body'].read().decode('utf-8')
    weather_data = json.loads(file_content)

    date = datetime.strptime(extract_date_from_filename(key), '%Y-%m-%d %H:%M:%S')
    
    partitioned_path = (
        f"{location}/year={date.year}/month={date.month:02d}/"
        f"day={date.day:02d}/hour={date.hour:02d}/weather_data.json"
    )

    s3.put_object(
        Bucket=processed_bucket,
        Key=partitioned_path,
        Body=file_content
    )

    crawlers = glue.list_crawlers()['CrawlerNames']
    if crawler_name not in crawlers:
        glue.create_crawler(
            Name=crawler_name,
            Role=RoleArn,
            DatabaseName=databaseName,
            Targets={'S3Targets': [{'Path': s3_path}]},
            TablePrefix=f"location_",
            SchemaChangePolicy={
                'UpdateBehavior': 'UPDATE_IN_DATABASE',
                'DeleteBehavior': 'LOG'
            }
        )
        glue.start_crawler(Name=crawler_name)
    else:
        glue.start_crawler(Name=crawler_name)

    return {
        'statusCode': 200,
        'body': json.dumps("Data partitioned, stored, and Glue Crawler handled successfully")
    }