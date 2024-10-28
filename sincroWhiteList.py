import json
import requests
import collections
import unicodedata
import string
import mysql.connector
from datetime import date
routeFiles = "/home/alain/Desktop/access_control_new/access_control_rb/"

with open(routeFiles+"config") as f:
    contentLines = f.readlines()

db_host = contentLines[0].split('=')[1].replace(" ", "").replace( '\n',"") 
db_database = contentLines[1].split('=')[1].replace(" ", "").replace( '\n',"") 
db_user = contentLines[2].split('=')[1].replace(" ", "").replace( '\n',"") 
db_pass = contentLines[3].split('=')[1].replace(" ", "").replace( '\n',"") 
idGateway = int(contentLines[4].split('=')[1].replace(" ", ""))
idBuilding = int(contentLines[5].split('=')[1].replace(" ", ""))
apiKey = contentLines[6].split('=')[1].replace(" ", "").replace( '\n',"")
urlService = contentLines[10].split('=')[1].replace(" ", "").replace( '\n',"")

f.close()

mydb_principal = mysql.connector.connect(
    host=db_host,
    user=db_user,
    password=db_pass,
    database=db_database
  )
query = mydb_principal.cursor()

today = date.today()
actual_date = today.strftime("%Y-%m-%d %H:%M:%S")
jsonRequestWhiteList = {'building_id' : idBuilding,'actual_date' :  actual_date}
headerPost = { 'content-type': 'application/json' ,'api-key':apiKey}
r = requests.post(urlService,data = json.dumps(jsonRequestWhiteList), headers =  headerPost )
respuesta = r.json()
whereDelete = ""
if respuesta != None:
	for x in range(0, len(respuesta)):

		id_whitelist_serv = str(respuesta[x]["id_whitelist"])
		access_code = str(respuesta[x]["access_code"])
		access_code_qr = str(respuesta[x]["access_code"])
		start_date = str(respuesta[x]["start_date"])
		end_date = str(respuesta[x]["end_date"])
		if x == 0: 
			whereDelete = whereDelete + id_whitelist_serv
		else:
			whereDelete = whereDelete + ","	 + id_whitelist_serv
		existe = 0

		query_whitelist = 'SELECT * FROM whitelist WHERE id_whitelist_serv=' + id_whitelist_serv
		query.execute(query_whitelist)
		resultwhitelist = query.fetchall()
		for row in resultwhitelist:
			existe = 1
			update_whitelist_code =  "UPDATE whitelist set access_code='" + access_code + "', access_code_qr='" + access_code_qr + "' WHERE id_whitelist_serv =  " + id_whitelist_serv
			query.execute(update_whitelist_code)

		if existe == 0:
			insert_whitelist_code = "INSERT INTO whitelist values(null,"+ id_whitelist_serv + ",'"+ access_code +"','" + access_code_qr + "','"+ start_date+"','" + end_date +  "')" 
			print(insert_whitelist_code)
			query.execute(insert_whitelist_code)
			#update_whitelist_code = "UPDATE whitelist set start_date = DATE_SUB(start_date, INTERVAL 4 HOUR),end_date = DATE_SUB(end_date, INTERVAL 4 HOUR) where id_whitelist_serv = "+ id_whitelist_serv +" "
			#query.execute(update_whitelist_code)

			
	
		if whereDelete != '':
			delete_whitelist = "DELETE FROM whitelist WHERE id_whitelist_serv not in (" + whereDelete + ")" 
			query.execute(delete_whitelist)


mydb_principal.commit()
query.close()
mydb_principal.close()
