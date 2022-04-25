import os
import datetime
import requests
import time
import boto3

OUTPUT_DIRS = ["./model/outputs/flow", "./model/outputs/temperature"]
BACKEND_URL = "http://127.0.0.1:8000/input_to_db"

def save_model_output():
    today = datetime.datetime.now(datetime.timezone.utc)

    # S3 bucket
    s3 = boto3.resource("s3")
    bucket = s3.Bucket("lake-tahoe-conditions")

    # TODO: possibly zip these files so we only need to send one request
    for dir in OUTPUT_DIRS:
        for filename in os.listdir(dir):
            # Send file to backend server if file's timestamp is greater than today
            # Parse timestamp from file
            file_date = datetime.datetime.strptime(filename, "%Y-%m-%d %H.npy")
            # Sets timezone to UTC without affecting other values
            file_date = file_date.replace(tzinfo=datetime.timezone.utc)
            if file_date > today:
                # Determine object key
                if dir.endswith("flow"):
                    objKey = f"flow/{filename}"
                else:
                    objKey = f"temperature/{filename}"

                # Upload file to s3
                filePath = f"{dir}/{filename}"
                # TODO: handle upload errors
                bucket.upload_file(filePath, objKey)

if __name__ == '__main__':
    save_model_output()
