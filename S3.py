
import boto3

import json   # stl class for un/marshalling
from typing import Union, Dict, List
from pathlib import Path
import credentials

import datetime
from datetime import timezone
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

    def uploadToS3(self, localFilePath: str, fileName: str, flow: bool) -> Union[bool, Dict[str, str]]:
        # For testing use next 2 lines
        # testDir = "save_model_output_test/"
        # key = f"{testDir}flow/{fileName}" if flow else f"{testDir}temperature/{fileName}"

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

    def getContents(self) -> Dict[str, List[str]]:
        # check if contents.json exists
        key: str = "contents.json"
        result: Dict[str, str] = self.__client.list_objects_v2(Bucket=self.__bucketName, Prefix=key)

        self.prettyPrint(result, title="Key Bucket Query Result:")

        contentsJSON: Dict[str, List[str]] = None
        prefixPath = "./outputs"
        fileLocation = f"{prefixPath}/{key}"

        if 'Contents' in result:
            print(f"{key} exists in the bucket.")

            # retreive contents.json
            self.__client.download_file(
                self.__bucketName,  # 'BUCKET_NAME'
                key,  # 'OBJECT_NAME'
                fileLocation  # 'FILE_NAME' destination to download file to
            )
            
            # load file into a json object
            f = open(fileLocation)
            contentsJSON = json.load(f)
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
        return contentsJSON

    def updateContents(self) -> Union[bool, Dict[str, str]]:
        """
        Approach: 
        1.) create and update contents.json
        2.) upload back to s3 bucket

        Warning: 
        this function must be used after uploading all files to the s3 bucket
        """
        # Remove old predictions from bucket
        for objType in ["temperature", "flow"]:
            response = self.__client.list_objects_v2(Bucket=self.__bucketName, Prefix=objType)
            objs = response.get("Contents")

            if objs == None:
                # No predictions for this type
                continue

            for obj in objs:
                # Delete predictions over 2 weeks old
                _, fileName = obj["Key"].split('/')
                objDate = datetime.datetime.strptime(fileName, "%Y-%m-%d %H.npy")
                # Predictions are made in the UTC timezone
                objDate = objDate.replace(tzinfo=timezone.utc)
                twoWeeksAgo = datetime.datetime.now(tz=timezone.utc) - datetime.timedelta(weeks=2)
                if objDate >= twoWeeksAgo:
                    continue
                
                print(f"Deleting {obj['Key']}...")
                self.__client.delete_object(Bucket=self.__bucketName, Key=obj["Key"])

        # get new contents.json
        contentsJSON = self.__createContents()

        prefixPath = "./outputs"
        key = "contents.json"

        fileLocation = f"{prefixPath}/{key}"

        # create and store json
        with open(fileLocation, "w") as f:
            json.dump(contentsJSON, f)

        # if testing uncomment next lines
        # key = "save_model_output_test/contents.json"

        # insert contents.json into s3 bucket
        return self.__insertToBucket(localFilePath=fileLocation, fileName=key)

    def __createContents(self) -> Dict[str, List[str]]:
        contents = {
            "flow": self.getAllFlowFilesFromBucket(),
            "temperature": self.getAllTemperatureFilesFromBucket()
        }
        return contents

    # TODO: not sure how to check if the request failed
    def deleteObject(self, objKey):
        self.__client.delete(Bucket=self.__bucketName, Key=objKey)

    def getAllFlowFilesFromDRS(self) -> List[str]:
        # return a list of filenames for objects in Flow Subdirectory in DRS
        return os.listdir(f"{self.__cwd}/outputs/flow")

    def getAllTemperatureFilesFromDRS(self) -> List[str]:
        # return a list of filenames for objects in Temperature Subdirectory in DRS
        return os.listdir(f"{self.__cwd}/outputs/temperature")

    def getAllFlowFilesFromBucket(self) -> List[str]:
        # return a list of filenames for objects in Flow Subdirectory in Bucket
        return self.getObjectsByKey("flow")

    def getAllTemperatureFilesFromBucket(self) -> List[str]:
        # return a list of filenames for objects in Temperature Subdirectory in Bucket
        return self.getObjectsByKey("temperature")

    def getObjectsByKey(self, key: str) -> List[str]:
        # gets all the objects with the matching prefix(inputted key)
        objectsInBucket = []
        response = self.__client.list_objects_v2(Bucket=self.__bucketName)
        for obj in response['Contents']:
            objName = obj["Key"]
            index = objName.find("/")
            if index == -1:  # index is not found
                continue
            dirName = objName[:index]  
            fileName = objName[index + 1:]
            if dirName == key:
                objectsInBucket.append(fileName)
        return objectsInBucket

    def prettyPrint(self, obj: Dict[str, Union[str, List[str]]], title: str = "MAP:") -> None:
        # prints map neatly for debugging
        print()
        print(title)
        for k, v in obj.items():
            print(f"{k} -> {v}")
            print()
        print()
        return None

    def prettyPrintArray(self, arr: List[str], title: str = "Array: ") -> None:
        # prints array neatly for debugging
        print()
        print(title)
        print()
        for v in arr:
            print(v)
        print()
        return None

# for testing purposes and debugging purposes
"""
if __name__ == "__main__":
    s3 = S3()

    response = s3.getContents()
    s3.prettyPrint(response, title="Contents.json: ")

    s3.prettyPrintArray(s3.getObjectsByKey("flow"), title="flow")
    print("=============================")
    s3.prettyPrintArray(s3.getObjectsByKey("temperature"), title="temperature")
    print("=============================")
    s3.prettyPrintArray(s3.getObjectsByKey("waveheight"), title="waveheight")
"""
