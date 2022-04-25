
import boto3

import json   # stl class for un/marshalling
from typing import Union, Dict, List
from pathlib import Path
import credentials

import os

class S3:

    def __init__(self) -> None:
        self.__client = boto3.client(
            service_name="s3",
            region_name="us-west-2",
            aws_access_key_id=credentials.aws_access_key_id,
            aws_secret_access_key=credentials.aws_secret_access_key
        )
        self.__bucketName = "lake-tahoe-conditions"
        self.__cwd = Path.cwd()
        return

    @staticmethod
    def uploadToS3(self, localFilePath: str, fileName: str, flow: bool) -> Union[bool, Dict[str, str]]:
        key = f"flow/{fileName}" if flow else f"temperature/{fileName}"

        response = self.__client.upload_file(
            localFilePath,  # path to the file that is to be uploaded in the local machine
            self.__bucketName,  # s3 bucket we will be adding the file to
            Key=key,  # path in the s3 bucket to where the file should be stored
        )

        if response == None:  # successful insertion into bucket
            message = {
                "message": "successful",
                "fileUploaded": localFilePath,
                "bucketName": self.__bucketName,
                "locationInBucket": key,
            }
            return True, message

        return False, {"message": "failed"}

    def __insertToBucket(self, localFilePath: str, fileName: str) -> Union[bool, Dict[str, str]]:
        # inserts files to bucket (not into a subdirectory)
        response = self.__client.upload_file(
            localFilePath,  # path to the file that is to be uploaded in the local machine
            self.__bucketName,  # s3 bucket we will be adding the file to
            Key=fileName,  # path in the s3 bucket to where the file should be stored
        )

        if response == None:  # successful insertion into bucket
            message = {
                "message": "successful",
                "fileUploaded": localFilePath,
                "bucketName": self.__bucketName,
                "locationInBucket": fileName,
            }
            return True, message

        return False, {"message": "failed"}

    @staticmethod
    def getContents(self) -> Dict[str, List[str]]:
        # check if contents.json exists
        key: str = "contents.json"
        result: Dict[str, str] = self.__client.list_objects_v2(Bucket=self.__bucketName, Prefix=key)

        print(result)

        contentsJSON: Dict[str, List[str]] = None
        prefixPath = "./tmp"
        fileLocation = f"{prefixPath}/{key}"

        if 'Contents' in result:
            print(f"{key} exists in the bucket.")
            # retreive contents.json

            self.__client.download_file(
                self.__bucketName,  # 'BUCKET_NAME'
                key,  # 'OBJECT_NAME'
                fileLocation  # 'FILE_NAME' destination to download file to
            )

            contentsJSON = json.load(f"{prefixPath}/{key}")
        else:
            print(f"{key} doesn't exist in the bucket.")
            # if it doesn't make a contents.json for the first time and insert to bucket
            contentsJSON = self.__createContents()

            # create and store json
            with open(fileLocation, "w") as f:
                json.dump(contentsJSON, f)

            # insert contents.json into s3 bucket
            self.__insertToBucket(localFilePath=fileLocation, fileName=key)

        # return contents.json after parsing into Dict[str, List[str]]
        print(contentsJSON)
        return contentsJSON

    def __createContents(self) -> Dict[str, List[str]]:
        contents = {
            "flow": self.getAllFlowFiles(),
            "temperature": self.getAllTemperatureFiles()
        }

        return contents

    def getAllFlowFiles(self) -> List[str]:
        # return a list of filenames for objects in Flow Subdirectory
        return os.listdir("dataretrieval/flow")

    def getAllTemperatureFiles(self) -> List[str]:
        # return a list of filenames for objects in Temperature Subdirectory
        return os.listdir("dataretrieval/temperature")


# for testing purposes
if __name__ == "__main__":
    s3 = S3()
    response = s3.getContents()
    print(response)
