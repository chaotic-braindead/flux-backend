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
        print(str(e))
        return {"message": str(e)}, 400


@app.get("/<id>")
def get_items_by_id(id):
    # get all objects under the given id and return expiring urls per object
    contents = s3.list_objects(Bucket=BUCKET, Prefix=f"uploads/{id}/").get(
        "Contents", []
    )
    oldest_obj = min(content["LastModified"] for content in contents)
    now = datetime.now(timezone.utc)
    elapsed = (now - oldest_obj).total_seconds()
    remaining = 24 * 3600 - int(elapsed)  # 24 hours (change if needed)

    if remaining <= 0:
        return []

    items = [
        {
            "url": s3.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": BUCKET,
                    "Key": content["Key"],
                },
                ExpiresIn=remaining,
            ),
            "Key": content["Key"],
            "Size": content["Size"],
        }
        for content in contents
    ]

    return {"remaining_time": remaining, "items": items}


if __name__ == "__main__":
    app.run()
