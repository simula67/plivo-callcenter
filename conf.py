import os

APP_URL = "plivocallcenter.herokuapp.com"

# Plivo Auth ID and Auth Token
PLIVO_AUTH_ID = os.environ.get('PLIVO_AUTH_ID')
PLIVO_AUTH_TOKEN = os.environ.get('PLIVO_AUTH_TOKEN')
DB_USERNAME=os.environ.get("DB_USERNAME")
DB_HOST=os.environ.get("DB_HOST")
DB_NAME=os.environ.get("DB_NAME")
DB_PASSWD=os.environ.get('DB_PASSWD')
