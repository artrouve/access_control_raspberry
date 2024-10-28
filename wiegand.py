#!/usr/bin/env python

import pigpio
import logging
import requests
import json
import mysql.connector
import datetime
import time
import re

import RPi.GPIO as GPIO


routeFiles = ""

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


class decoder:

   """
   A class to read Wiegand codes of an arbitrary length.
   The code length and value are returned.
   """

   def __init__(self, pi, gpio_0, gpio_1, callback, bit_timeout=6):

      """
      Instantiate with the pi, gpio for 0 (green wire), the gpio for 1
      (white wire), the callback function, and the bit timeout in
      milliseconds which indicates the end of a code.
      The callback is passed the code length in bits and the value.
      """
      self.pi = pi
      self.gpio_0 = gpio_0
      self.gpio_1 = gpio_1

      self.callback = callback

      self.bit_timeout = bit_timeout

      self.in_code = False

      self.pi.set_mode(gpio_0, pigpio.INPUT)
      self.pi.set_mode(gpio_1, pigpio.INPUT)

      self.pi.set_pull_up_down(gpio_0, pigpio.PUD_UP)
      self.pi.set_pull_up_down(gpio_1, pigpio.PUD_UP)

      self.cb_0 = self.pi.callback(gpio_0, pigpio.FALLING_EDGE, self._cb)
      self.cb_1 = self.pi.callback(gpio_1, pigpio.FALLING_EDGE, self._cb)

   def _cb(self, gpio, level, tick):

      """
      Accumulate bits until both gpios 0 and 1 timeout.
      """

      if level < pigpio.TIMEOUT:

         if self.in_code == False:
            self.bits = 1
            self.num = 0

            self.in_code = True
            self.code_timeout = 0
            self.pi.set_watchdog(self.gpio_0, self.bit_timeout)
            self.pi.set_watchdog(self.gpio_1, self.bit_timeout)
         else:
            self.bits += 1
            self.num = self.num << 1

         if gpio == self.gpio_0:
            self.code_timeout = self.code_timeout & 2 # clear gpio 0 timeout
         else:
            self.code_timeout = self.code_timeout & 1 # clear gpio 1 timeout
            self.num = self.num | 1

      else:

         if self.in_code:

            if gpio == self.gpio_0:
               self.code_timeout = self.code_timeout | 1 # timeout gpio 0
            else:
               self.code_timeout = self.code_timeout | 2 # timeout gpio 1

            if self.code_timeout == 3: # both gpios timed out
               self.pi.set_watchdog(self.gpio_0, 0)
               self.pi.set_watchdog(self.gpio_1, 0)
               self.in_code = False
               self.callback(self.bits, self.num,self.gpio_0,self.gpio_1)

   def cancel(self):

      """
      Cancel the Wiegand decoder.
      """

      self.cb_0.cancel()
      self.cb_1.cancel()


if __name__ == "__main__":
    
   import time
   import pigpio
   import wiegand
   import subprocess 

   idboard = idGateway



   def callback_(bits, value,gpio_0,gpio_1):

      try:
         gi = gpio_0
         wi = gpio_1
         now = datetime.datetime.now()
         datetoprint = now.strftime("%d/%m/%Y %H:%M:%S")
         print("*********************************************")
         print(datetoprint)
         print("INTENTO APERTURA PUERTA: gi_0:",gi," wi_1:",wi)
         val = "{:34b}".format(value)
         val = re.sub("[^0-1]","0",val) 
         print("ANTES DE PROCESAR:"+val)
         #if len(val)<34:
         #	val = val[:-1]
         #else:
         val = val[1:-1]	
         print(val)
         print("bits={} value={}".format(bits, val))
         card_id = int(val,2)
         
         print("Card ID: {:10d}".format(card_id))

         #se debe realizar consulta a la base de datos local y verificar si el codigo de acceso es valido
         val = "{:10d}".format(card_id)
         val = "0"+val.replace(" ","")
         print("targeta:" + val + "")
         access_code_qr = val
         if(len(access_code_qr)!=11 and access_code_qr[0:3]!="053" and access_code_qr[0:3]!="052"):
           return ""
         mydb_principal = mysql.connector.connect(
           host=db_host,
           user=db_user,
           password=db_pass,
           database=db_database
         )
         query = mydb_principal.cursor()

         print("ACCESSO BASE DATOS LOCAL: PUERTA I0:",gi," I1:",wi)
         print("ACCESSO BASE DATOS LOCAL: CODIGO:",val)

         
         print("SOLICITANDO APERTURA PUERTA: I0:",gi," I1:",wi)
         print("CONSULTADO PUERTA EN BASE DE DATOS: I0:",gi," I1:",wi)
         query_gate_string = "SELECT id_access_gate,name_access_gate,obs_access_gate,go,wo,id_access_gate_serv  FROM access_gate where gi = "+ str(gi) +" and wi = "+ str(wi) +" and gateway_id = " + str(idboard) + " " 
         query.execute(query_gate_string)
         resultgate = query.fetchall()
         id_access_gate = 0
         name_access_gate = 0
         obs_access_gate = 0
         id_access_gate_serv = 0
         go = 0
         wo = 0
         for gate in resultgate:
            id_access_gate = gate[0]
            name_access_gate = gate[1]
            obs_access_gate = gate[2]
            go = gate[3]
            wo = gate[4]
            id_access_gate_serv = gate[5]
         print("ID PUERTA:",id_access_gate)
         print("NOMBRE PUERTA:",name_access_gate)
         print("OBS PUERTA:",obs_access_gate)
         print("SALIDAS GPIO: go: " + str(go) + " wo: " + str(wo))


         #SE VERIFICA QUE TIPO DE CODIGO ES:
         #CODIGOS Y REPRESENTACIONES:
         #051 RESIDENTES
         #052 RESIDENTES TEMPORALES
         #053 VISITAS TEMPORALES

         acess_code_qr = val;
         person_type = acess_code_qr[0:3]
         print("TIPO ACCESO:",acess_code_qr[0:3])

         person_type_id = 0;
         query_person_string=""
         if person_type!="053" and person_type!="052":
            #ES UN CODIGO DE RESIDENTE
            query_person_string = decodeQRtime(acess_code_qr[1:])
            person_type_id = 1;

         if person_type=="052":
            #ES UN CODIGO DE RESIDENTE TEMPORAL
            query_person_string = "SELECT id_resident_temp_serv FROM residents_temps WHERE access_code_qr='"+access_code_qr+"'"
            person_type_id = 2;

         if person_type=="053":
            #ES UN CODIGO DE ACCESO
            query_person_string = "SELECT id_whitelist_serv FROM whitelist WHERE access_code_qr='"+access_code_qr+"' and now()>=start_date and now()<= end_date"
            #print(query_person_string)
            person_type_id = 3; 
         
         print("CONSULTADO CODIGO EN BASE DATOS:")

         query.execute(query_person_string)
         resultperson = query.fetchall()
         open_dor = False
         id_person = 0
         for person in resultperson:
            open_dor = True
            id_person = person[0]

         if open_dor == True:

            GPIO.setmode(GPIO.BCM)
            GPIO.setup(go, GPIO.OUT)
            GPIO.output(go, GPIO.LOW)
            time.sleep(0.3)

            GPIO.setup(go, GPIO.OUT)
            GPIO.output(go, GPIO.HIGH)
            
            GPIO.setup(go, GPIO.OUT)
            GPIO.output(go, GPIO.HIGH)


            print("CONSULTA CODIGO GENERAL DE APERTURA DE PUERTA")
            query_general_access_code = "SELECT general_access_code  FROM config"
            query.execute(query_general_access_code)
            result_general_access_code = query.fetchall()
            general_access_code = result_general_access_code[0][0];
            print("CODIGO GENERAL DE APERTURA: " + str(general_access_code))

            print("ENVIANDO SALIDAS GPIO: go: " + str(go) + " wo: " + str(wo))
            program = '/home/alain/Desktop/Test/send_wiegand/tx_WD/tx_WD'
            #process = subprocess.run([program, '-g'+str(go), '-w'+str(wo), '-s26', general_access_code])
            #if process.returncode == 0:
            if True:
               #SE SIMULA UNA EJECUCION CORRECTA DEL QR   
               print(f'ENVIO SALIDAS CORRECTO')
               print('INSERTANDO LOG DE APERTURA EN BASE DE DATOS')

               id_resident = None
               id_resident_temp = None
               id_whitelist = None

               if person_type_id == 1:
                  id_resident = id_person

               if person_type_id == 2:
                  id_resident_temp = id_person
               
               if person_type_id == 3:
                  id_whitelist = id_person

               now = datetime.datetime.now()
               
               insert_access_log_string = "INSERT INTO access_log (date,type_person_access,resident_id,resident_temp_id,whitelist_id,access_gate_id,updated_serv) VALUES (%s,%s,%s,%s,%s,%s,%s)"
               values_insert_access_log = (now.strftime("%Y-%m-%d %H:%M:%S"), person_type_id, id_resident,id_resident_temp,id_whitelist,id_access_gate_serv,False)
               query.execute(insert_access_log_string, values_insert_access_log)
               mydb_principal.commit()
               print('INSERCION DE LOG EXITOSA')
               print('SE PROCEDE A CONSUMO DE SERVICIO DE ACUTLIZACION DE CODIGO Y REGISTRO DE LOG')
               GPIO.setup(go, GPIO.OUT)
               GPIO.output(go, GPIO.HIGH)


         
         else:
            print('CÓDIGO INVALIDO, SE NIEGA EL ACCESO, SE ENVIA CODIGO ERRONEO')
            program = '/home/alain/Desktop/Test/send_wiegand/tx_WD/tx_WD'
            #process = subprocess.run([program, '-g'+str(go), '-w'+str(wo), '-s26', ""])
            if True == False:
            #if True == True:
               #SE SIMULA UNA EJECUCION CORRECTA DEL QR   
               #print(f'ENVIO SALIDAS CORRECTO: {process.stdout}')
               print("ENVIO SALIDAS CON CODIGO INCORRECTO EXITOSO")

         query.close()
         mydb_principal.close()
         print("*********************************************")
      
      except Exception as e:
         print("Error "+ str(e))
#         logger.error('ERROR: '+ str(e))
         exit()

   def restaurarNumero(numero_transformado, digito):
       
      if digito == '0':
        numero_original = numero_transformado[-1] + numero_transformado[:-1]
      elif digito == '1':
        numero_original = numero_transformado[1:6]+ numero_transformado[0] + numero_transformado[6:]
      elif digito == '2':
        numero_original = numero_transformado[1:3] + numero_transformado[0] + numero_transformado[3:]
      elif digito == '3':
        numero_original = numero_transformado[1:7] + numero_transformado[0] + numero_transformado[7]
      elif digito == '4':
        numero_original = numero_transformado[1:6] + numero_transformado[0] + numero_transformado[7] + numero_transformado[6]
      elif digito == '5':
        numero_original = numero_transformado[5] + numero_transformado[1:5] + numero_transformado[6] + numero_transformado[7] + numero_transformado[0]
      elif digito == '6':
        numero_original = numero_transformado[6:] + numero_transformado[1:6] + numero_transformado[0]
      elif digito == '7':
        numero_original = numero_transformado[5:] + numero_transformado[1:5] + numero_transformado[0]
      elif digito == '8':
        numero_original = numero_transformado[5:7] + numero_transformado[0] + numero_transformado[2:5] + numero_transformado[7] + numero_transformado[1]
      elif digito == '9':
        numero_original = numero_transformado[1] + numero_transformado[3:7] + numero_transformado[0] + numero_transformado[2] + numero_transformado[7]
      else:
        raise ValueError("El dígito ingresado debe ser un número del 0 al 9.")

      return numero_original

   def decodeQRtime(value):
      
      #se debe extraer el delta 
      where_resident = ""
      RESULT_QUERY = ""
      mydb_principal = mysql.connector.connect(
        host=db_host,
        user=db_user,
        password=db_pass,
        database=db_database
      )

      query = mydb_principal.cursor()
      query_get_delta = "SELECT delta_time,date_pivote,code_building FROM config " 
      query.execute(query_get_delta)
      result = query.fetchall()
      delta = result[0][0]
      date_pivot = result[0][1]
      code_building = result[0][2]	
      query.close()
      mydb_principal.close()

      timestamp_local_gmt = datetime.datetime.now()
      now_utc = timestamp_local_gmt.timestamp() + float(delta)
      now_corrected = now_utc -20
      k = 0
      i = -20
      while i<15:
         i = i + 1
         now_corrected = now_corrected + 1
         now = datetime.datetime.fromtimestamp(now_corrected)
         date_pivot = int(date_pivot)
         while date_pivot + 31536000 < now_corrected:
            date_pivot = date_pivot + 31536000
         date_pivot_diff = int(now_corrected - date_pivot);
         date_pivot_diff = str(date_pivot_diff)


         C1 = date_pivot_diff
         primer_caracter = C1[len(C1) - 6]
         C1 = primer_caracter + C1[len(C1) - 5] + C1[len(C1) - 4] + C1[len(C1) - 3] +  C1[len(C1) - 2]+  C1[len(C1) - 1];
         print("*********************************************C1:" + C1)

         CODE_TO_DECODE = value[4:9]
         LAST_DIGIT_CODE = value[9]
         FIRST_DIGIT_CODE = value[0]
         CODE_TO_DECODE = restaurarNumero(value[1:9],value[9])

         #print("CODIGO ORDENADO + EDIFICIO", FIRST_DIGIT_CODE + CODE_TO_DECODE + LAST_DIGIT_CODE)

         VERIFICATION_CODE_ID_RESIDENT = (FIRST_DIGIT_CODE + CODE_TO_DECODE + LAST_DIGIT_CODE)[0:4]
         VERIFICATION_CODE_ID_RESIDENT_MINUS_1 = str(int((FIRST_DIGIT_CODE + CODE_TO_DECODE + LAST_DIGIT_CODE)[0:4]) - 1)

         CODE_TO_DECODE = str(int(CODE_TO_DECODE) -  int(code_building)*int(LAST_DIGIT_CODE))

         if len(CODE_TO_DECODE) < 8:
            CODE_TO_DECODE = "0" + CODE_TO_DECODE

         CODE_TO_DECODE = FIRST_DIGIT_CODE + CODE_TO_DECODE + LAST_DIGIT_CODE
         CODE_TO_DECODE = str(int(CODE_TO_DECODE) - int(C1))
         VALIDATOR_BUILDING = int(code_building)
         ORIGINAL_CODE_0 = str(int(CODE_TO_DECODE))
         
         if len(ORIGINAL_CODE_0) < 10:
            ORIGINAL_CODE_0 = "0" + ORIGINAL_CODE_0

         if i==-9:
            where_resident = "code_id = '"+ ORIGINAL_CODE_0[4:] +"' "
         if i>-9:
            where_resident = where_resident + "OR code_id = '"+ ORIGINAL_CODE_0[4:] +"' "
         #print("VERIFICACION:"+VERIFICATION_CODE_ID_RESIDENT)
         #print("CODIGO RESIDENTE: " + ORIGINAL_CODE_0[4:])
      where_resident =  "SELECT id_resident_serv FROM residents WHERE ((code_id_validator = '"+ VERIFICATION_CODE_ID_RESIDENT +"' or code_id_validator='"+ VERIFICATION_CODE_ID_RESIDENT_MINUS_1 +"') and (" + where_resident + ")) or (access_code_qr ="+ value +" and TIMESTAMPDIFF(SECOND, date_update_qr, now()) < 10)"
      #where_resident =  "SELECT id_resident_serv FROM residents WHERE (code_id_validator = '"+ VERIFICATION_CODE_ID_RESIDENT +"' or code_id_validator='"+ VERIFICATION_CODE_ID_RESIDENT_MINUS_1 +"') and (" + where_resident + ")"
      print("Consulta residente:",where_resident )	
      return where_resident

   def callback_wa(bits, value):

      #DEBE LLAMAR A LA FUNCION QUE REALMENTE REALIZA LA APERTURA
       wiegand.encoder(pi, 23, 24, callback_)

   def callback_wb(bits, value):

      #DEBE LLAMAR A LA FUNCION QUE REALMENTE REALIZA LA APERTURA
       wiegand.encoder(pi, 23, 24, callback_)

   
   try:

        now = datetime.datetime.now()

        datetoprint = now.strftime("%d/%m/%Y %H:%M:%S")
        print(datetoprint)
        pi = pigpio.pi()

        GPIO.setmode(GPIO.BCM)

        GPIO.setup(27, GPIO.OUT)
        GPIO.setup(18, GPIO.OUT)
        GPIO.setup(17, GPIO.OUT)

        GPIO.output(27, GPIO.HIGH)
        GPIO.output(18, GPIO.HIGH)
        GPIO.output(17, GPIO.HIGH)

        wa = wiegand.decoder(pi, 10, 23, callback_)
        wb = wiegand.decoder(pi, 4, 2, callback_)
        wc = wiegand.decoder(pi, 15, 3, callback_)
       

        time.sleep(360000000)
   

        wa.cancel()
        wb.cancel()
        wc.cancel()
        pi.stop()

   except Exception as e:
        print("Error "+ str(e))
#        logger.error('ERROR: '+ str(e))
        exit()
