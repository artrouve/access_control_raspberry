import json
import requests
import collections
import unicodedata
import string
import mysql.connector
import time
import ntplib
import datetime

routeFiles = "/home/alain/Desktop/access_control_new/access_control_rb/"

with open(routeFiles+"config") as f:
    contentLines = f.readlines()

db_host = contentLines[0].split('=')[1].replace(" ", "").replace( '\n',"") 
db_database = contentLines[1].split('=')[1].replace(" ", "").replace( '\n',"") 
db_user = contentLines[2].split('=')[1].replace(" ", "").replace( '\n',"") 
db_pass = contentLines[3].split('=')[1].replace(" ", "").replace( '\n',"") 
f.close()

mydb_principal = mysql.connector.connect(
    host=db_host,
    user=db_user,
    password=db_pass,
    database=db_database
  )
query = mydb_principal.cursor()
query_ntp_server = "SELECT url_ntp FROM config"
query.execute(query_ntp_server)
resultconfig = query.fetchall()
url_ntp = resultconfig[0][0]

#SE DEBE CALCULAR EL DELTA, DEL TIEMPO
timestamp_local_gmt = datetime.datetime.now()
ntp_client = ntplib.NTPClient()
response_ntp = ntp_client.request(url_ntp)
timestamp_serv_gmt = (datetime.datetime.fromtimestamp(response_ntp.tx_time)).timestamp()
delta = round(timestamp_serv_gmt - timestamp_local_gmt.timestamp(),4)
print("valor delta: ",delta)
#SE GUARDA LA DIFERENCIA EN MILISEGUNDOS
update_config =  "UPDATE config set delta_time=" + str(delta) + "";
query.execute(update_config)
mydb_principal.commit()
query.close()
mydb_principal.close()
