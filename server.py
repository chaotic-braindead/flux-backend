import boto3
from flask import Flask, request
from flask_cors import CORS
from dotenv import load_dotenv
import os
from datetime import datetime, timezone
from botocore.config import Config

load_dotenv()

BUCKET = os.getenv("BUCKET")

s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("AWS_SECRET_KEY"),
    region_name=os.getenv("REGION"),
    config=Config(s3={"addressing_style": "virtual"}),
)

app = Flask(__name__)
# CORS(app, origins=['<url to s3 static site>']) change if prod
CORS(app)


@app.post("/get-upload-link")
def upload():
    try:
        # generates a presigned url so that aws takes care of uploading
        # instead of the lambda function (faster processing uploads + less lambda bandwidth usage + not exposing API keys in client)
        data = request.get_json()
        content_type = data.get("contentType", "application/octet-stream")
        key = f"uploads/{data["id"]}/{data['filename']}"
        resp = s3.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": BUCKET,
                "Key": key,
                "ContentType": content_type,
            },
            ExpiresIn=60 * 5,  # upload link valid for 5 minutes,
        )
        # the frontend must perform a PUT request to the url returned,
        # passing the same form and the headers should be: { "Content-Type": file.type }
        return {"url": resp}
    except Exception as e:
        return {"message": str(e)}


@app.get("/<id>")
def get_items_by_id(id):
    # get all objects under the given id and return expiring urls per object
    contents = s3.list_objects(Bucket=BUCKET, Prefix=f"uploads/{id}/").get(
        "Contents", []
    )
    if not contents:
        return {"remaining_time": 0, "items": []}

    # get oldest object and check if url is expired
    oldest_obj = min(content["LastModified"] for content in contents)
    now = datetime.now(timezone.utc)
    elapsed = (now - oldest_obj).total_seconds()
    remaining = 24 * 3600 - int(elapsed)  # 24 hours (change if needed)

    response = {"remaining_time": remaining, "items": []}

    # add items if not expired
    if remaining > 0:
        for content in contents:
            url = s3.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": BUCKET,
                    "Key": content["Key"],
                },
                ExpiresIn=remaining,
            )
            response["items"].append(
                {
                    "url": url,
                    "Key": content["Key"],
                    "Size": content["Size"],
                }
            )
    return response


if __name__ == "__main__":
    app.run()
