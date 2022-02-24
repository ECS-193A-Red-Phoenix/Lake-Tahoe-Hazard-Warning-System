import os
import datetime

OUTPUT_DIRS = ["./outputs/flow", "./outputs/temperature"]

def save_model_output():
    today = datetime.datetime.now(datetime.timezone.utc)

    for dir in OUTPUT_DIRS:
        for file in os.listdir(dir):
            print(file)
            # TODO upload file to database if timestamp is greater than today


if __name__ == '__main__':
    save_model_output()
