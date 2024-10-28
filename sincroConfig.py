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
urlService = contentLines[11].split('=')[1].replace(" ", "").replace( '\n',"")

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
jsonRequestConfig = {'building_id' : idBuilding}
headerPost = { 'content-type': 'application/json' ,'api-key':apiKey}
r = requests.post(urlService,data = json.dumps(jsonRequestConfig), headers =  headerPost )
respuesta = r.json()
whereDelete = ""
if respuesta != None:
	for x in range(0, len(respuesta)):

		id_config_serv = str(1)
		general_access_code = str(respuesta[x]["general_access_code"])
		url_ntp = str(respuesta[x]["url_ntp"])
		date_pivote = str(respuesta[x]["date_pivote"])
		code_building = str(respuesta[x]["code_building"])
		mqtt_host = str(respuesta[x]["mqtt_host"])
		mqtt_port = str(respuesta[x]["mqtt_port"])
		mqtt_user = str(respuesta[x]["mqtt_user"])
		mqtt_pass = str(respuesta[x]["mqtt_pass"])

		if x == 0: 
			whereDelete = whereDelete + id_config_serv
		else:
			whereDelete = whereDelete + ","	 + id_config_serv
		existe = 0

		query_whitelist = 'SELECT * FROM config'
		query.execute(query_whitelist)
		resultconfig = query.fetchall()
		for row in resultconfig:
			existe = 1
			update_config =  "UPDATE config set general_access_code='" + general_access_code + "',url_ntp='" + url_ntp + "',date_pivote='" + date_pivote + "', code_building = '" + code_building + "', mqtt_host = '" + mqtt_host + "', mqtt_port = '" + mqtt_port + "', mqtt_user = '" + mqtt_user + "', mqtt_pass = '" + mqtt_pass + "'"
			query.execute(update_config)

		if existe == 0:
			insert_config = "INSERT INTO config values(null,'"+ general_access_code +"','"+date_pivote+"','"+url_ntp+"','0','"+code_building+"'"+mqtt_host+"'"+mqtt_port+"'"+mqtt_user+"'"+mqtt_pass+"')"
			query.execute(insert_config)


mydb_principal.commit()
query.close()
mydb_principal.close()
