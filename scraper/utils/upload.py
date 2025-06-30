
import boto3
import gzip
import json
from io import BytesIO
from datetime import datetime

def upload_articles_to_s3(articles, bucket_name, category):
    """Compress articles to .json.gz and upload to S3"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{category}_articles_{timestamp}.json.gz"

    # Compress JSON data
    buffer = BytesIO()
    with gzip.GzipFile(filename='data.json', mode='wb', fileobj=buffer) as gz:
        gz.write(json.dumps(articles, ensure_ascii=False, indent=2).encode('utf-8'))
    buffer.seek(0)

    # Upload to S3
    s3 = boto3.client('s3')
    s3.upload_fileobj(buffer, bucket_name, filename)

    return filename
