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
REGION=your region
```

5. Start server

```
flask --app server run -h localhost --debug # restarts on save
```

## Usage

### Uploading (POST `/get-upload-link`)

Note: the backend does not directly upload a file. Instead, it returns a presigned upload url.

First, perform a POST request on the `/get-upload-link` endpoint with the filename, folder name/id, expirationHour, and contentType in the request body to get the presigned S3 upload url (see [server.py](server.py))

Next, use the presigned url and perform a PUT request with the file in the request body and add the file's content type in the headers (see [server.py](server.py))

Note: This function writes expiry metadata per image bc afaik there is no way to check metadata for folders, only files

### Viewing contents of a folder (GET `/<id>`)

Perform a GET request on the `/<id>` endpoint to get the remaining time left and all items in the bucket along with their respective presigned urls which expire based on configured expiration time. (change if needed)

Note: AWS only allows a minimum of 1 day lifecycle for objects before automatic expiration/deletion. It is also not guaranteed that objects will be deleted exactly after 1 day, hence the expiring url to prevent access after expiration.

## Additional info

To be hosted as a Lambda function linked to an API Gateway (automated using Zappa)
