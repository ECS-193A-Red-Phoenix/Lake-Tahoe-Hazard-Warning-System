import sys
import os.path


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python upload_s3.py <file path>")
        sys.exit(0)

    file_path = sys.argv[1]
    file_name = os.path.basename(file_path)

    if not os.path.isfile(file_path):
        print(f"Error: Could not find file '{file_path}'")
        sys.exit(0)
    
    from S3 import S3
    s3 = S3()
    s3._S3__insertToBucket(file_path, file_name)

    print(f"Successfully uploaded '{file_name}' to S3")
    print("Done!")
