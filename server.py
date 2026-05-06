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
        now = datetime.now(timezone.utc)
        expiration_in_seconds = data["expirationHours"] * 60 * 60
        expiration_date = int(now.timestamp() + expiration_in_seconds)

        key = f"uploads/{data["id"]}/{data['filename']}"
        resp = s3.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": BUCKET,
                "Key": key,
                "ContentType": content_type,
                "Metadata": {"expiration_date": str(expiration_date)},
            },
            ExpiresIn=60 * 5,  # upload link valid for 5 minutes,
        )
        # the frontend must perform a PUT request to the url returned,
        # passing the same form and the headers should be: { "Content-Type": file.type }
        return {"url": resp}
    except Exception as e:
        return {"message": str(e), "url": None}


@app.get("/<id>")
def get_items_by_id(id):
    # get all objects under the given id and return expiring urls per object
    contents = s3.list_objects(Bucket=BUCKET, Prefix=f"uploads/{id}/").get(
        "Contents", []
    )
    if not contents:
        return {"remaining_seconds": 0, "items": []}

    # get expiry metadata and check if url is expired
    metadata = s3.head_object(Bucket=BUCKET, Key=contents[0]["Key"]).get("Metadata", {})

    expiration_timestamp = datetime.fromtimestamp(
        int(metadata.get("expiration_date", 0)), tz=timezone.utc
    )
    now = datetime.now(timezone.utc)

    if now >= expiration_timestamp:
        return {"remaining_seconds": 0, "items": []}

    remaining_seconds = int((expiration_timestamp - now).total_seconds())
    response = {"remaining_seconds": remaining_seconds, "items": []}
    for content in contents:
        url = s3.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": BUCKET,
                "Key": content["Key"],
            },
            ExpiresIn=remaining_seconds,
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
