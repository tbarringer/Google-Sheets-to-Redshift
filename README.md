# Creating a Cost-Effective, Rapid Data Pipeline Between Google Sheets and AWS Redshift
Description and code for sending data from Google Sheets to AWS Redshift

## Introduction

We’re going to create a simple, efficient data pipeline to send data from Google Sheets to AWS Redshift. This pipeline provides an easy way to send data from a non-technical application (Google Sheets) to a company’s database. Additionally, this pipeline can be easily set up to run automatically on a schedule, allowing the application to fulfill its role autonomously. One potential use case is the maintenance of a lookup table in Google Sheets (accessible and easy-to-use for general business users) which can be used in more rigorous applications later, such as queries within Redshift. 

To create this pipeline, we will be using Google Sheets, AWS S3, and AWS Redshift to store our data and AWS Lambda functions to send data between them. As mentioned previously, Lambda functions are able to be scheduled, allowing this system to update as frequently as you would like. 

## Using the Google Sheets API

Our first step in the process is to allow programmatic access to Google Sheets via its API. We will create our Google Sheet, go to the Google developers console to setup the API, and collect our credentials for this API.

1.	Create your Google Sheet that you wish to (ultimately) upload to Redshift. I have named mine “State-City-Key” with two columns, State and City. 

![Google Sheet](screenshots/Google1.PNG)

2.	Next, go to console.developers.google.com and create a project if you have not done so already. Choose a name for your project and leave ‘Location’ set to ‘No Organization’. Click CREATE. 

![Google API](screenshots/Google2.PNG)

3.	 Within the project, click the “Library” on the left-side menu. Search for the Google Drive API and select it. Click “Enable”. 

![Google API Library](screenshots/Google4.PNG)

![Google Drive API](screenshots/Google5.PNG)

4.	Click CREATE CREDENTIALS to enter Google’s credentials wizard. 

![Google Drive API](screenshots/Google6.PNG) 

For “Which API are you using” select “Google Drive API”. “Where will you be calling the API from” is “Web server”. You will be processing “Application data” and will not be using this API with the App or Compute Engine. Click “What credentials do I need?” 

![Google Drive API](screenshots/Google7.PNG)

5.	Enter a service account name, mark the role as Editor, and keep the key type as JSON. Click Continue. 

![Google Drive API](screenshots/Google8.PNG)

6.	A JSON file will be automatically downloaded to your computer. Keep this file safe; it has the access keys to your Google API. Open this file. There will be an entry for ‘client_email’ – copy this email address. It will be required in the next step. 
7.	Go to your Google Sheet created in Step 1. Click ‘File’ and then ‘Share’. Enter the email address from step 6 into the email field and click ‘Share’. This allows your API access to the Google Sheet. 
8.	Repeat Steps 3-7 for the Google Sheets API. 

We’re now ready to access our data in Google Sheets programmatically via a Lambda function in AWS! 

## Setting up an AWS S3 bucket

This next part is easy – we’re going to create an S3 bucket on AWS to hold our data that was uploaded from Google Sheets in a CSV file. 
1.	On the AWS console, go to S3 and click Create Bucket
2.	Enter a compliant bucket name and click next

![AWS S3 Bucket CreationI](screenshots/S1.PNG)

3.	Click through the next screens (keeping the default values) until you can click “Create Bucket” 
That’s it! You have an S3 bucket live on AWS. 

## Creating a Lambda function to send Google Sheets to AWS S3

Our next section is using AWS Lambda to send our data from Google Sheets to our S3 bucket. AWS Lambda is a serverless computing platform for AWS. It basically allows you to run functions in the cloud with virtually no infrastructure. You only pay for what you use so there are potentially enormous cost savings as well. Additionally, Lambda makes it easy to run functions on a schedule so we can keep our data pipeline flowing. 

Note: everything required for this Lambda function, including packages and a zipped file, is included in this repo in the "GoogleSheets-to-S3_Lambda" folder

1.	From the AWS Console go to Lambda and click “Create Function”. 
2.	Select “Author From Scratch”, create a function name, and select Python 3.7 for the runtime. Click “Create function” 

![AWS Lambda](screenshots/S3L1.PNG)

3.	Under function code, select “Upload from .zip”. 

![AWS Lambda](screenshots/S3L2.PNG)

We need to do this because we’re going to have to use a couple libraries not included in the basic Lambda package. We will create a new directory on our local computer, create a file in the directory that holds our Lambda function, and pip install libraries directly to the directory. We will then zip the contents of this directory and upload the file to AWS. 
4.	On your local computer, create a new directory. In that directory, use “pip install gspread oauth2client --target .” to install two dependencies directly into your directory (we will be using both gpsread and oauth2 in our lambda function)

![AWS Lambda](screenshots/S3L3.PNG)

5.	Create a new file in the directory named lambda_function.py (name is important); this will be where your code lives. First, import all of your required libraries:
```python
import json
import csv
import os
import boto3
import gspread
from oauth2client.service_account import ServiceAccountCredentials
```

Next, we will create a function that will load environment varibales containing our Google API credentials into a keyfile dictionary. It is important to keep the '.replace('\\n','\n') for the private key as Python will parse the newline character in an odd way. 

```python
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
```

We will now begin writing the main portion of our lambda function and start with using our credentials to access the Google API. Gspread is our improted library that we use with the API to access the data that we have in Google. 

```python
def lambda_handler(event, context):

	# use creds to create a client to interact with the Google Drive API
	scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
	keys = create_keyfile_dict()
	creds = ServiceAccountCredentials.from_json_keyfile_dict(keys, scope)
	client = gspread.authorize(creds)
```

Finally, we will open our Google Sheet, grab all of its values, write it to a csv, and upload that csv to our S3 bucket. 

```python

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
```

6.	Zip the entire directory (highlight all of the files, including the libraries) and send it to a Zip file
7.	Upload this ZIP to AWS Lambda. If the upload was successful you should see your code in the built-in editor.

![AWS Lambda](screenshots/S3L4.PNG)

8.	We’re now going to add our environment variables to the Lambda function and encrypt them. The first step is translating the values from your JSON credentials file (from Google) into environment variables. Enter each key value pair from the JSON file, making sure you match the key names that you have entered in your Lambda code. At a high level, the function will take the environment values you entered and transform them into a new JSON dictionary that Google’s authentication service is able to use to verify access to its APIs.

![AWS Lambda](screenshots/S3L5.PNG)

9.	The next step encrypts these environment variables to add an additional layer of security for your data pipeline. In the AWS console, search for and open the Key Management System. Click “Create a key” to get started. 

![AWS Lambda](screenshots/S3L6.PNG)

10.	In the Key creation wizard, select “Symmetric” and then click Next. Choose a name for your key. Under key administrators, choose your AWS IAM role. For key usage permissions, select your AWS IAM role again. Review your key policy and click Finish.
11.	Go back to your Lambda function and open the “Encryption Configuration” dropdown. Check the “Enable helpers for encryption in transit”. Then, in the “AWS KMS key to encrypt in transit” text box, begin typing the name of your key you just created. 

![AWS Lambda](screenshots/S3L7.PNG)

Select this key. Now, you can press the “Encrypt” button in your key value pairs to encrypt them right in Lambda! 

12.	Now it is time to test our function. To do this, make sure you click ‘Save’ (running tests in Lambda will only work on the latest saved version). To test, click the “Test” button in the upper right corner. Leave the default values for the test and add any event name you would like. Click the “Test” button again to execute your Lambda function! You can see output from the function in the terminal window below your function. Also take this time to check your S3 bucket; you should have a csv file that matches your Google Sheets data. 
13.	The default Lambda execution timeout rate is 3 seconds. You may require more time for your function to execute – change it to 1 minute to make sure it has enough time. Also, if you are using this pipeline within a VPC, make sure you have selected it in the “Network” section of the Lambda function page.  
14.	To automate our Lambda function, we are going to create a trigger which will execute the function every hour. To start, find the 'Add trigger' button on your Lambda's Designer page (it's right about where you can see the code for the function).

![AWS Lambda](screenshots/S3L8.PNG)

15.	Next, select CloudWatch event for the trigger (this feature allows functions to run on a schedule). Select 'Create a New Rule' to design your schedule. For 'Rule Name' add a unique/easy to identify name and add a 'Rule desciption' if you wish. Under 'Rule type' we're going to select 'Schedule expression' as we want to run our function every hour. Finally, add your desired rate in the 'Schedule expression' box, make sure 'Enable trigger' is checked, and click 'Add' to attach this trigger to the Lambda function. 

![AWS Lambda](screenshots/S3L9.PNG)

16.	Now when you are back on the Lambda's designer page you should see 'CloudWatch Events' under your function. Your Lambda will now execute according to the schedule you set, automatically! 

![AWS Lambda](screenshots/S3L10.PNG)

## Creating a stored procedure in AWS Redshift

In this section, we’re going to create a [stored procedure](https://docs.aws.amazon.com/redshift/latest/dg/stored-procedure-create.html) in AWS Redshift. This stored procedure will save our query that we will be using to move our data from S3 to Redshift. Stored procedures are great because they make it easy to call complicated queries (both in terms of code and credentials/permissions) programmatically – making this a perfect application for our data pipeline. 

1.	We are now ready to prepare our Redshift database for the incoming data. Go to the Redshift console in AWS. Open up the Query Editor in AWS (You can also use DataGrip, etc).
2.	The first query in Redshift will be to create the table that will import the data. In my example, I am creating a simple table with two columns, State and City.  I use the "public" schema because this is a demo, but you should rarely/never use the "public" schema and instead use a schema like etl, analytics, etc.

![AWS Redshift](screenshots/Redshift_Query1.PNG)

```
CREATE TABLE public.city_state (
	state VARCHAR
	, city VARCHAR
	
);
```

3.	The next query will be to create a Stored Procedure in Redshift. As mentioned before, stored procedures are queries you can “Save” in Redshift and call them later with a simple “Call” query. They are valuable because the permissions of the stored procedure can be set within Redshift itself, giving us one less thing to worry about when we’re using Lambda to programmatically access Redshift. One important note - make sure that the Redshift user has the correct Redshift permissions to copy a file into a specific table in the schema. The stored procedure query is below: 

![AWS Lambda](screenshots/Redshift_Query2.PNG)

```
CREATE PROCEDURE s3_csv_import()
AS $$
	BEGIN
	copy city_state from 's3://<YOUR-BUCKET-NAME-HERE>/<FILENAME>.csv'
	credentials 'YOUR-CREDENTIALS-HERE'
	IGNOREHEADER 1
	csv;
	END;
$$
LANGUAGE plpgsql
;
```

4.	We are now able to call this procedure by creating a query with “CALL <stored procedure name>" and this will execute the query as if it were just entered in Redshift. 
5.	We’re now ready for our final step – calling this stored procedure from Lambda! 

## Using AWS Lambda to move data between S3 and Redshift

We’re now ready for the final step in the process: creating a Lambda function that will send data from our S3 bucket to our Redshift database. 

Note: everything required for this Lambda function, including packages and a zipped file, is included in this repo in the "S3-to-Redshift_Lambda" folder

1.	The trickiest part of accessing Redshift via Lambda functions is due to the nature of Lambda’s stored libraries and using a Postgresql database adapter for Python. Luckily, some amazing people have helped us out and done the hard work for us and made their work available on github [here](https://github.com/jkehler/awslambda-psycopg2). This package allows us to use psycopg2 within Lambda with all dependencies fully installed. Follow the instructions on the github readme and download the package. Place the correct version of psycopg2 in a new directory (I used the Python 3.7 version). 
2.	In this directory, create another file called lambda_function.py (sound familiar)? 
3.	Add the following code to your Lambda function (quick tip: the user/password for Redshift you're using in this function can be input as encrypted environment variables, as in the first Lambda functoin we wrote. I left them explicitly decalred in the example to clearly show the connection string required):

```python
import psycopg2

def lambda_handler(event, context):
    
    #connect to Redshift 
	#note: for security purposes, you should put the secure values in the below
	# string as encrypted environment variables in Lambda
    con = psycopg2.connect(dbname='<DBNAME>', port='<PORT>', host='<CLUSTER_NAME>.<CLUSTER_ID>.<REGION>.redshift.amazonaws.com', user='<REDSHIFT_USERNAME>', password='<REDSHIFT_PASSWORD>')
    
    #sql query that calls the stored procedure in Redshift
    sql="""
        CALL s3_csv_import();
        COMMIT;
        """ 
    
    #Connect to the Redshift database and execute the query 
    con.set_session(readonly=False)
    cur = con.cursor()
    cur.execute(sql)
    
    #close all connections 
    cur.close()
    con.close()
```
Note: to find the 'host' value for your Redshift database, go to the Redshift console. Click on 'Clusters' in the menu on the left side of the page. Select your cluster from the list by clicking on its name. Near the top of the page will be something that says "ENDPOINT" with a URL after it. The URL WITHOUT the port number at the end is the full value required for the 'host' field.

4.	Zip the entire contents of this directory.
5.	In the AWS Lambda console, create a new Lambda function and upload the zip file that you just created. 
6.	As before, create a Test event and run the test on Lambda. If everything executes correctly, go to Redshift and check your table to verify the contents of the csv uploaded as intended. 

![AWS Lambda](screenshots/Redshift_Query3.PNG)
Congratulations, you now have a data pipeline from Google Sheets to AWS Redshift! 
7.	You can now create a CloudWatch event to run this function automatically so the pipeline continues to flow. 
