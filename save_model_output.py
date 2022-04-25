import os
import datetime
import boto3

OUTPUT_DIRS = ["./model/outputs/flow", "./model/outputs/temperature"]

# Send new predictions to S3
def save_model_output():
    # S3 bucket
    s3 = boto3.resource("s3")
    bucket = s3.Bucket("lake-tahoe-conditions")

    today = datetime.datetime.now(datetime.timezone.utc)
    for dir in OUTPUT_DIRS:
        for fileName in os.listdir(dir):
            # Only upload new predictions
            fileDate = datetime.datetime.strptime(fileName, "%Y-%m-%d %H.npy")
            # TODO: use PST to avoid confusion?
            fileDate = fileDate.replace(tzinfo=datetime.timezone.utc)
            if fileDate <= today:
                continue

            # Upload new prediction to S3
            localFilePath = f"{dir}/{fileName}"
            if dir.endswith("flow"):
                objKey = f"flow/{fileName}"
            else:
                objKey = f"temperature/{fileName}"
            # TODO: handle upload errors
            bucket.upload_file(localFilePath, objKey)

if __name__ == '__main__':
    save_model_output()
