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
urlService = contentLines[9].split('=')[1].replace(" ", "").replace( '\n',"")

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

		id_residenttemp_serv = str(respuesta[x]["id_resident_temp"])
		access_code = str(respuesta[x]["access_code"])
		access_code_qr = str(respuesta[x]["access_code"])
		start_date = str(respuesta[x]["start_date"])
		end_date = str(respuesta[x]["end_date"])
		if x == 0: 
			whereDelete = whereDelete + id_residenttemp_serv
		else:
			whereDelete = whereDelete + ","	 + id_residenttemp_serv
		existe = 0

		query_resident = 'SELECT * FROM residents_temps WHERE id_resident_temp_serv=' + id_residenttemp_serv
		query.execute(query_resident)
		resultresident = query.fetchall()
		for row in resultresident:
			existe = 1
			update_resident_code =  "UPDATE residents_temps set access_code='" + access_code + "', access_code_qr='" + access_code_qr + "' WHERE id_resident_temp_serv =  " + id_residenttemp_serv
			query.execute(update_resident_code)

			
		if existe == 0:
			insert_resident_code = "INSERT INTO residents_temps values(null,"+ id_residenttemp_serv + ",'"+ start_date+"','" + end_date + "','"+ access_code +"','" + access_code_qr + "')" 
			query.execute(insert_resident_code)

			
	delete_residents = "DELETE FROM residents_temps WHERE id_resident_temp_serv not in (" + whereDelete + ")" 
	query.execute(delete_residents)


mydb_principal.commit()
query.close()
mydb_principal.close()
