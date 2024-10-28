
import json
import random
import time
import requests
import collections
import unicodedata
import string
import mysql.connector
import os
import paho.mqtt.client as mqtt_client
from paho.mqtt.client import MQTTv5


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

f.close()

mydb_principal = mysql.connector.connect(
    host=db_host,
    user=db_user,
    password=db_pass,
    database=db_database
  )
query = mydb_principal.cursor()
query_mqtt = "SELECT mqtt_host,mqtt_port,mqtt_user,mqtt_pass FROM config"
query.execute(query_mqtt)
resultconfig = query.fetchall()
mqtt_host = resultconfig[0][0]
mqtt_port = resultconfig[0][1]
mqtt_user = resultconfig[0][2]
mqtt_pass = resultconfig[0][3]


#BROKER = 'localhost'
BROKER = mqtt_host
PORT = int(mqtt_port)
PROTOCOL = 5

TOPIC = "updateqrresident/"+str(idBuilding)
# generate client ID with pub prefix randomly
CLIENT_ID = "updateqrresident-sub-{id}".format(id=random.randint(0, 1000))
USERNAME = mqtt_user
PASSWORD = mqtt_pass
FLAG_CONNECTED = 0

# Upon connection, Paho calls the on_connect() function, which can be defined as needed.
# It is the callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc, properties=None):

    global FLAG_CONNECTED
    if str(rc) == "Success":
        FLAG_CONNECTED = 1
        print("Connected to MQTT Broker with status: {rc}".format(rc=rc))
        # Subscribing in on_connect() means that if we lose the connection and
        # reconnect then subscriptions will be renewed.
        client.subscribe(TOPIC, qos=0, options=None, properties=None)
        print("Subscribed to topic `{topic}`".format(topic=TOPIC))
        print("Expect to receive automated messages every 2 seconds.\n")
    else:
        print("Failed to connect, return code: {rc}".format(rc=rc))

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    
    try:
        print("Received `{payload}` from topic `{topic}`".format(
            payload=msg.payload.decode(), topic=msg.topic))

        messageJson = json.loads(msg.payload.decode())
        id_resident = messageJson["id_resident"];
        access_code_qr = messageJson["access_code_qr"];
        update_qr_code =  "UPDATE residents set access_code_qr='" + access_code_qr + "' , date_update_qr = now() where id_resident_serv ="+id_resident+"";
        print(update_qr_code)
        query.execute(update_qr_code)
        mydb_principal.commit()
    except Exception as ex:
        os._exit(1)    


def connect_mqtt():
    # Creates an instance of the MQTT client
    client = mqtt_client.Client(client_id=CLIENT_ID, protocol=MQTTv5)
    # Logs in if there is an existing user defined on the broker side
    client.username_pw_set(USERNAME, PASSWORD)
    client.on_connect = on_connect
    client.on_message = on_message
    # Broker address and port defined on broker side, keep-alive of choice
    client.connect(BROKER, port=PORT, keepalive=60, clean_start="MQTT_CLEAN_START_FIRST_ONLY")
    return client

def run():
    client = connect_mqtt()
    client.loop_start()
    time.sleep(2000000000)

    if FLAG_CONNECTED:
#        publish(client)
        print("CONNECTED")
    else:
        client.loop_stop()

if __name__ == '__main__':
    run()
