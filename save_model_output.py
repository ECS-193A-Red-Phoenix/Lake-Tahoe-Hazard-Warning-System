import os
import datetime
import requests
import time

import S3

OUTPUT_DIRS = ["./outputs/flow", "./outputs/temperature"]
BACKEND_URL = "http://127.0.0.1:8000/input_to_db"

def save_model_output() -> None:
    today = datetime.datetime.now(datetime.timezone.utc)

    s3 = S3.S3()  # s3 client with methods specific to our needs

    for localDir in OUTPUT_DIRS:
        bucketSubDirectory: str = flowTemperaturePicker(localDir)
        for filename in os.listdir(localDir):
            # Send file to backend server if file's timestamp is greater than today
            # Parse timestamp from file
            file_date = datetime.datetime.strptime(filename, "%Y-%m-%d %H.npy")
            # Sets timezone to UTC without affecting other values
            file_date = file_date.replace(tzinfo=datetime.timezone.utc)

            if file_date > today:
                # Read and send file
                fileLocation = f"{localDir}/{filename}"
                flow = (bucketSubDirectory == "flow")  # if false then file will be uploaded to temperature
                successful, msg = s3.uploadToS3(fileLocation, filename, flow)
                if successful:
                    print(s3.prettyPrint(msg, title="File Upload Response: ")) 
                else:
                    print("Upload Failed!")
    
    # update contents.json
    _, response = s3.updateContents()
    print(response)
    return None

"""
For Testing

def save_model_output() -> None:
    today = datetime.datetime.now(datetime.timezone.utc)

    s3 = S3.S3()  # s3 client with methods specific to our needs

    for localDir in OUTPUT_DIRS:
        bucketSubDirectory: str = flowTemperaturePicker(localDir)
        for filename in os.listdir(localDir):
            # Send file to backend server if file's timestamp is greater than today
            # Parse timestamp from file
            file_date = datetime.datetime.strptime(filename, "%Y-%m-%d %H.npy")
            # Sets timezone to UTC without affecting other values
            file_date = file_date.replace(tzinfo=datetime.timezone.utc)

            if file_date < today:
                # Read and send file
                fileLocation = f"{localDir}/{filename}"
                flow = (bucketSubDirectory == "flow")  # if false then file will be uploaded to temperature
                successful, msg = s3.uploadToS3(fileLocation, filename, flow)
                if successful:
                    print(s3.prettyPrint(msg, title="File Upload Response: ")) 
                else:
                    print("Upload Failed!")
    
    # update contents.json
    _, response = s3.updateContents()
    print(response)
    
    return None
"""

def flowTemperaturePicker(directoryPath: str) -> str:
    # returns the lowest directory in path
    lastDirectoryIndex: int = directoryPath.rfind("/")
    return directoryPath[lastDirectoryIndex + 1:]

if __name__ == '__main__':
    save_model_output()
