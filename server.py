import boto3
from flask import Flask, request
from flask_cors import CORS
from dotenv import load_dotenv
import os

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
        folder = request.form["id"]
        filename = request.form["filename"]
        key = f"uploads/{folder}/{filename}"
        buff = request.files["file"]
        response = s3.put_object(
            Bucket=BUCKET,
            Key=key,
            Body=buff,
            ContentType=request.form["content_type"],
            ContentLength=buff.content_length,
            ContentDisposition=request.form["content_disposition"],
        )
    except Exception as e:
        return {"message": e}, 400
    return {"message": "ok"}, 201


@app.get("/<id>")
def get_items_by_id(id):
    return s3.list_objects(Bucket=BUCKET, Prefix=f"uploads/{id}/")


app.run()
