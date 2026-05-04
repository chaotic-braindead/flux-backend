import boto3
from flask import Flask, request
from flask_cors import CORS
from dotenv import load_dotenv
import os
from datetime import datetime, timezone

load_dotenv()

BUCKET = os.getenv("BUCKET")

s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("AWS_SECRET_KEY"),
)

app = Flask(__name__)
# CORS(app, origins=['<url to s3 static site>']) change if prod
CORS(app)


@app.post("/get-upload-link")
def upload():
    # the frontend's request body must be a FormData instance; ex: const formData = new FormData(); look it up frontend peeps
    try:
        folder = request.form["id"]
        buff = request.files["file"]
        key = f"uploads/{folder}/{buff.filename}"
        # generates a presigned url so that aws takes care of uploading
        # instead of the lambda function (faster processing uploads + less lambda bandwidth usage + not exposing API keys in client)
        resp = s3.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": BUCKET,
                "Key": key,
                "Body": buff,
                "ContentType": buff.content_type,
                "ContentLength": buff.content_length,
                "ContentDisposition": f"inline; filename={buff.filename}",
            },
            ExpiresIn=60 * 5,  # upload link valid for 5 minutes,
        )
        # the frontend must perform a 'PUT' request to the url returned,
        # passing the same form and the headers should be: {"Content-Type": file.type || "application/octet-stream"}
        return {"url": resp}
    except Exception as e:
        print(str(e))
        return {"message": str(e)}, 400


@app.get("/<id>")
def get_items_by_id(id):
    # get all objects under a certain uuid and return expiring urls per object
    contents = s3.list_objects(Bucket=BUCKET, Prefix=f"uploads/{id}/").get(
        "Contents", []
    )
    resp = []
    for content in contents:
        last_modified = content["LastModified"]
        # calculate if expired
        now = datetime.now(timezone.utc)
        elapsed = (now - last_modified).total_seconds()
        remaining = 24 * 3600 - int(elapsed)
        if remaining <= 0:
            expires_in = 0
            url = None
        else:
            expires_in = remaining
            url = s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": BUCKET, "Key": content["Key"]},
                ExpiresIn=expires_in,
            )
        resp.append({"url": url, **content})
    return resp


if __name__ == "__main__":
    app.run()
