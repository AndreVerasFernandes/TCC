import boto3
from botocore.exceptions import ClientError
import os
import dotenv

dotenv.load_dotenv()

# Now you can access them seamlessly
url = os.environ.get("URL")
access_key = os.environ.get("<ACCESS_KEY_ID>")
secret_key = os.environ.get("<SECRET_ACCESS_KEY>")

# Initialize the R2 client using the S3-compatible API
s3 = boto3.client(
    service_name="s3",
    endpoint_url=url,  # Replace with your Account ID
    aws_access_key_id= access_key,                        # Replace with your Access Key
    aws_secret_access_key=secret_key,                # Replace with your Secret Key
    region_name="auto",  # Cloudflare R2 manages regions automatically
)
bucket_name = "tcc"
file_path = "/workspaces/TCC/images.webp"
object_key = "images.webp"

try:
    s3.upload_file(file_path, bucket_name, object_key)
    print(f" Successfully uploaded {file_path} to R2!")
except ClientError as e:
    print(f"Upload failed: {e}")

try:
    response = s3.list_objects_v2(Bucket=bucket_name)
    if "Contents" in response:
        for obj in response["Contents"]:
            print(f"File: {obj['Key']} | Size: {obj['Size']} bytes")
    else:
        print("Bucket is empty.")
except ClientError as e:
    print(f"Error listing objects: {e}")

try:
    s3.download_file(bucket_name, object_key, "downloaded_image.png")
    print(" Download successful!")
except ClientError as e:
    print(f"Download failed: {e}")

