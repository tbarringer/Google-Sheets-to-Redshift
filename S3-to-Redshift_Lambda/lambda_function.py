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