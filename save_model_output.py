import os
import datetime
import boto3

OUTPUT_DIRS = ["./model/outputs/flow", "./model/outputs/temperature"]
BACKEND_URL = "http://127.0.0.1:8000/input_to_db"

# Send new predictions to S3
def save_model_output():
    # S3 bucket
    s3 = boto3.resource("s3")
    bucket = s3.Bucket("lake-tahoe-conditions")

    today = datetime.datetime.now(datetime.timezone.utc)
    # TODO: possibly zip these files so we only need to send one request
    for dir in OUTPUT_DIRS:
        for fileName in os.listdir(dir):
            fileDate = datetime.datetime.strptime(fileName, "%Y-%m-%d %H.npy")
            # TODO: use PST to avoid confusion?
            fileDate = fileDate.replace(tzinfo=datetime.timezone.utc)
            if fileDate <= today:
                # Assume old predictions already in S3
                continue

            # Upload new prediction to S3
            # Determine object key
            if dir.endswith("flow"):
                objKey = f"flow/{fileName}"
            else:
                objKey = f"temperature/{fileName}"

            filePath = f"{dir}/{fileName}"
            # TODO: handle upload errors
            bucket.upload_file(filePath, objKey)

if __name__ == '__main__':
    save_model_output()
