import boto3
from flask import Flask, request
from flask_cors import CORS
from dotenv import load_dotenv
import os
from uuid import uuid4

load_dotenv()

BUCKET = "wormhole-parallel-bucket"

s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("AWS_SECRET_KEY"),
)

app = Flask(__name__)
CORS(app)


@app.post("/upload")
def upload():
    try:
        id = uuid4()
        files = request.files.getlist("files")

        for file in files:
            s3.put_object(
                Bucket=BUCKET,
                Key=f"uploads/{id}/{file.filename}",
                Body=file,
                ContentType=request.form["content_type"],
                ContentLength=file.content_length,
                ContentDisposition=request.form["content_disposition"],
            )
    except Exception as e:
        return {"message": str(e)}, 400
    return {"message": "ok", "id": id}, 201


@app.get("/<id>")
def get_items_by_id(id):
    return s3.list_objects(Bucket=BUCKET, Prefix=f"uploads/{id}/")


app.run()
