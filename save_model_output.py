import os
import datetime
import requests
import time

OUTPUT_DIRS = ["./model/outputs/flow", "./model/outputs/temperature"]
BACKEND_URL = "http://127.0.0.1:8000/input_to_db"

def save_model_output():
    today = datetime.datetime.now(datetime.timezone.utc)

    # TODO: possibly zip these files so we only need to send one request
    for dir in OUTPUT_DIRS:
        for filename in os.listdir(dir):
            # Send file to backend server if file's timestamp is greater than today
            # Parse timestamp from file
            file_date = datetime.datetime.strptime(filename, "%Y-%m-%d %H.npy")
            # Sets timezone to UTC without affecting other values
            file_date = file_date.replace(tzinfo=datetime.timezone.utc)
            if file_date > today:
                # Read and send file
                file = open(f"{dir}/{filename}", mode="rb")
                data = file.read()
                response = requests.post(BACKEND_URL, files={
                    "file": data,
                })

                print(f"Response code: {response}")

                # Finished with file
                file.close()

if __name__ == '__main__':
    save_model_output()
