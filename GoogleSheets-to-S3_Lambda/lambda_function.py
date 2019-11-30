import json
import csv
import os
import boto3
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def create_keyfile_dict():
	variables_keys = {
		"type": os.environ.get("TYPE"),
        "project_id": os.environ.get("PROJECT_ID"),
        "private_key_id": os.environ.get("PRIVATE_KEY_ID"),
        "private_key": os.environ.get("PRIVATE_KEY").replace('\\n','\n'),
        "client_email": os.environ.get("CLIENT_EMAIL"),
        "client_id": os.environ.get("CLIENT_ID"),
        "auth_uri": os.environ.get("AUTH_URI"),
        "token_uri": os.environ.get("TOKEN_URI"),
        "auth_provider_x509_cert_url": os.environ.get("AUTH_PROVIDER_X509_CERT_URL"),
        "client_x509_cert_url": os.environ.get("CLIENT_X509_CERT_URL")
	}
	return variables_keys

def lambda_handler(event, context):

	# use creds to create a client to interact with the Google Drive API
	scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
	keys = create_keyfile_dict()
	creds = ServiceAccountCredentials.from_json_keyfile_dict(keys, scope)
	client = gspread.authorize(creds)

	# Find a workbook by name and open the first sheet
	# Make sure you use the right name here.
	sheet = client.open("<GOOGLE_SHEET_NAME>").sheet1

	# Extract and print all of the values
	resultsList = sheet.get_all_values()

	with open("/tmp/output.csv", "w", newline="") as f:
		writer = csv.writer(f)
		writer.writerows(resultsList)
	
	client = boto3.client('s3')
	client.upload_file('/tmp/output.csv', '<S3_BUCKET_NAME>', '<CSV_FILENAME>')
	
	
