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
urlService = contentLines[13].split('=')[1].replace(" ", "").replace( '\n',"")

f.close()

mydb_principal = mysql.connector.connect(
    host=db_host,
    user=db_user,
    password=db_pass,
    database=db_database
  )
query = mydb_principal.cursor(dictionary = True)

access_logs = []

query_access_logs = 'SELECT * FROM access_log WHERE updated_serv=0'
query.execute(query_access_logs)
result_access_logs = query.fetchall()
for row in result_access_logs:
	access_log = collections.OrderedDict()
	access_log["id_access_log"] = row["id_access_log"]
	access_log['date'] = str(row["date"])
	access_log['type_person_access'] = row["type_person_access"]
	access_log['resident_id'] = row["resident_id"]
	access_log['resident_temp_id'] = row["resident_temp_id"]
	access_log['whitelist_id'] = row["whitelist_id"]
	access_log['access_gate_id'] = row["access_gate_id"]
	access_logs.append(access_log)
	


jsonRequestAccessLogs = {'building_id' : idBuilding,'access_logs' : access_logs}
print(json.dumps(jsonRequestAccessLogs))
headerPost = { 'content-type': 'application/json' ,'api-key':apiKey}
r = requests.post(urlService,data = json.dumps(jsonRequestAccessLogs), headers =  headerPost )
print(r)
respuesta = r.json()
print(respuesta)
respuesta = respuesta["access_return"]
whereDelete = ""
if respuesta != None:
	for x in range(0, len(respuesta)):

		id_access_log_update = str(respuesta[x]["id_access_log"])
		type_person_access = str(respuesta[x]["type_person_access"])
		new_qr_code = str(respuesta[x]["new_access_code"])
		
		update_access_log =  "UPDATE access_log set updated_serv=1 WHERE id_access_log =  " + id_access_log_update
		query.execute(update_access_log)

		if type_person_access == "1":
			id_resident = str(respuesta[x]["id_resident"])
			update_resident_qr_code =  "UPDATE residents set access_code_qr='"+new_qr_code+"' WHERE id_resident =  " + id_resident
			query.execute(update_resident_qr_code)

		if type_person_access == "2":
			id_resident_temp = str(respuesta[x]["id_resident_temp"])
			update_resident_temp_qr_code =  "UPDATE residents_temp set access_code_qr='"+new_qr_code+"' WHERE id_resident_temp =  " + id_resident_temp
			query.execute(update_resident_temp_qr_code)

		if type_person_access == "3":
			id_whitelist = str(respuesta[x]["id_whitelist"])
			update_whitelist_temp_qr_code =  "UPDATE whitelist set access_code_qr='"+new_qr_code+"' WHERE id_whitelist =  " + id_whitelist
			query.execute(update_whitelist_temp_qr_code)


mydb_principal.commit()
query.close()
mydb_principal.close()
