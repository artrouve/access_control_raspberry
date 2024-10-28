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
urlService = contentLines[12].split('=')[1].replace(" ", "").replace( '\n',"")

f.close()

mydb_principal = mysql.connector.connect(
    host=db_host,
    user=db_user,
    password=db_pass,
    database=db_database
  )
query = mydb_principal.cursor()

jsonRequestGates = {'building_id' : idBuilding , 'gateway_id' : idGateway }
headerPost = { 'content-type': 'application/json' ,'api-key':apiKey}
r = requests.post(urlService,data = json.dumps(jsonRequestGates), headers =  headerPost )
respuesta = r.json()
whereDelete = ""
if respuesta != None:
	for x in range(0, len(respuesta)):

		id_access_gate_serv = str(respuesta[x]["id_access_gate"])
		name_access_gate = str(respuesta[x]["name_access_gate"])
		obs_access_gate = str(respuesta[x]["obs_access_gate"])
		gateway_id = str(respuesta[x]["gateway_id"])
		
		wi = str(respuesta[x]["wi"])
		gi = str(respuesta[x]["gi"])
		wo = str(respuesta[x]["wo"])
		go = str(respuesta[x]["go"])
		
		if x == 0: 
			whereDelete = whereDelete + id_access_gate_serv
		else:
			whereDelete = whereDelete + ","	 + id_access_gate_serv
		existe = 0

		query_gate = 'SELECT * FROM access_gate WHERE id_access_gate_serv=' + id_access_gate_serv
		query.execute(query_gate)
		resultgate = query.fetchall()
		for row in resultgate:
			existe = 1
			update_gate =  "UPDATE access_gate set wi=" + wi + ",gi=" + gi + ",wo=" + wo + ",go=" + go + ",name_access_gate ='"+name_access_gate+"',obs_access_gate ='"+obs_access_gate+"' WHERE id_access_gate_serv =  " + id_access_gate_serv
			query.execute(update_gate)

			
		if existe == 0:
			insert_gate = "INSERT INTO access_gate values(null,"+ id_access_gate_serv + ",'"+ name_access_gate +"','" + obs_access_gate + "',"+gateway_id+","+ wi+","+ gi+","+ wo+","+ go+")" 
			query.execute(insert_gate)

			
	delete_gates = "DELETE FROM access_gate WHERE id_access_gate_serv not in (" + whereDelete + ")"
	query.execute(delete_gates)


mydb_principal.commit()
query.close()
mydb_principal.close()
