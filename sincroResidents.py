import json
import requests
import collections
import unicodedata
import string
import mysql.connector

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
urlService = contentLines[8].split('=')[1].replace(" ", "").replace( '\n',"")

f.close()

mydb_principal = mysql.connector.connect(
    host=db_host,
    user=db_user,
    password=db_pass,
    database=db_database
  )
query = mydb_principal.cursor()

jsonRequestResidents = {'building_id' : idBuilding }
headerPost = { 'content-type': 'application/json' ,'api-key':apiKey}
r = requests.post(urlService,data = json.dumps(jsonRequestResidents), headers =  headerPost )
respuesta = r.json()

whereDelete = ""
if respuesta != None:
	for x in range(0, len(respuesta)):

		id_resident_serv = str(respuesta[x]["id_resident"])
		access_code = str(respuesta[x]["access_code"])
		#access_code_qr = str(respuesta[x]["access_code"])

		code_id = str(respuesta[x]["code_id"])
		code_id_validator = str(respuesta[x]["code_id_validator"])

		if x == 0: 
			whereDelete = whereDelete + id_resident_serv
		else:
			whereDelete = whereDelete + ","	 + id_resident_serv
		existe = 0

		query_resident = 'SELECT * FROM residents WHERE id_resident_serv=' + id_resident_serv
		query.execute(query_resident)
		resultresident = query.fetchall()
		for row in resultresident:
			existe = 1
			update_resident_code =  "UPDATE residents set access_code='" + access_code + "',code_id='"+ code_id+"',code_id_validator = '"+code_id_validator+"'  WHERE id_resident_serv =  " + id_resident_serv
			query.execute(update_resident_code)

			
		if existe == 0:
			insert_resident_code = "INSERT INTO residents values(null,"+ id_resident_serv + ",'"+ access_code +"',null,null,'" + code_id + "','" + code_id_validator + "')"
			query.execute(insert_resident_code)

			
	delete_residents = "DELETE FROM residents WHERE id_resident_serv not in (" + whereDelete + ")" 
	query.execute(delete_residents)


mydb_principal.commit()
query.close()
mydb_principal.close()
