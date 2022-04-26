import os
import datetime
import boto3
import json

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
                objType = "flow"
            else:
                objType = "temperature"
            objKey = f"{objType}/{fileName}"

            print(f"Uploading {fileName}...", end="", flush=True)

            try:
                bucket.upload_file(localFilePath, objKey)

                # Update contents.json in S3
                objs = bucket.objects.all()
                objKeys = [obj.key for obj in objs]
                if "contents.json" not in objKeys:
                    # Create new contents if it doesn't exist
                    contents = {
                        "flow": [],
                        "temperature": []
                    }
                else:
                    # Load existing contents from S3
                    with open("contents.json", "wb+") as contentsFileObj:
                        bucket.download_fileobj("contents.json", contentsFileObj)
                        contentsFileObj.seek(0)
                        contents = json.load(contentsFileObj)

                # Update contents
                contents[objType].append(fileName)

                # Save and upload new contents file
                with open("contents.json", "w+") as contentsFileObj:
                    json.dump(contents, contentsFileObj)

                with open("contents.json", "rb") as contentsFileObj:
                    bucket.upload_fileobj(contentsFileObj, "contents.json")

                # Don't need local copy of contents
                os.remove("contents.json")
            except Exception as e:
                # Print any errors that occur while uploading
                print("failed!")
                print(e)
                continue

            # Success
            print("done.")

if __name__ == '__main__':
    save_model_output()
