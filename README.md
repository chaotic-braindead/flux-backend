# Flux Backend

Server to help upload file/s to an S3 bucket

### Setup

1. Clone the repo

```
git clone https://github.com/chaotic-braindead/flux-backend.git
```

2. Init virtual environment

```
cd flux-backend
python -m venv venv
source venv/bin/activate # linux/mac
source venv/Scripts/activate # windows
```

3. Install requirements

```
pip install -r requirements.txt
```

4. Create .env file

```
AWS_ACCESS_KEY=your access key here
AWS_SECRET_KEY=your secret key here
BUCKET=your bucket name here
```

5. Start server

```
flask --app server run --debug # restarts on save
```

## Usage

### Uploading (POST `/get-upload-link`)

Note: the backend does not directly upload a file. Instead, it returns a presigned upload url.

First, perform a POST request on the `/get-upload-link` endpoint with the file in the request body to get the presigned S3 upload url (see [server.py](server.py))

Next, use the presigned url and perform a PUT request with the file also in the request body (see [server.py](server.py))

### Viewing contents of a folder (GET `/<id>`)

Perform a GET request on the `/<id>` endpoint to get all items in the bucket along with their respective presigned urls.

## Additional info

To be hosted as a Lambda function linked to an API Gateway (automated using Zappa)
