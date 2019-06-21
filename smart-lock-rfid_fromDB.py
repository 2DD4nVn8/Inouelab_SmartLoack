import RPi.GPIO as GPIO
import datetime
import binascii
import nfc
import ndef
import time
import csv
import pandas as pd
import os

from threading import Thread, Timer

filename = "/home/pi/WorkSpace/SmartLock/Inouelab_RFID_DB.csv"


# Identifying device 
identifying_code = {
  "Student card":'0110',
  "iphone":'0139',
  "Android":'0134',
  "Transportation card": '0101'
}

GP_OUT = 4

TIME_CYCLE = 1.0
TIME_INTERVAL = 0.2
TIME_WAIT = 0.1

SIT_ID_CARD_OFFSET = 3
SIT_ID_CARD_NUMBER_OF_CHARS = 7
state_of_key = False

return_to_zero = False
#0010215723010000
#12250001120412d3189c1b
#01120412d3189c1b

#0010100123010000
#61205401101100d10fd901
#01101100d10fd901

remote_target_212f = nfc.clf.RemoteTarget("212F")
remote_target_424f = nfc.clf.RemoteTarget("424F")

#service_code = 0x090f
service_code = 0x010b

#sys_code_felica = 0xfe00
sys_code_felica = 0x0003
sys_code_student_card = 0x8277

class MyCardReader(object):

  def toggle_key(self):
    global state_of_key
    if state_of_key == True:
      self.unlock_key()
    else:
      self.lock_key()

  def lock_key(self):
    print(str(datetime.datetime.now()) + " "  + "Lock key")
    global state_of_key
    global return_to_zero
    state_of_key = True
    servo = GPIO.PWM(GP_OUT, 50)
    servo.start(0)
    time.sleep(0.2)
    servo.ChangeDutyCycle(2.5)
    time.sleep(0.5)
    servo.stop()

  def unlock_key(self):
    print (str(datetime.datetime.now()) + " " + "Unlock key")
    global state_of_key
    global return_to_zero
    state_of_key = False
    servo = GPIO.PWM(GP_OUT, 50)
    servo.start(0)
    time.sleep(0.2)
    servo.ChangeDutyCycle(7.25)
    time.sleep(0.5)
    servo.stop()

  def read_rfid(self):
    # reset flag
    registered_flag = False
    clf = nfc.ContactlessFrontend('usb')
    try:
      target_res = clf.sense(
        remote_target_212f,
        remote_target_424f,
        iterations=int(TIME_CYCLE//TIME_INTERVAL)+1,
        interval=TIME_INTERVAL)
      if target_res != None:
        #read registered
        IC_DB = pd.read_csv(filename, index_col=[0, 1])
        #print(IC_DB)
        registered_sit_ids = IC_DB.index.get_level_values('student_id').drop_duplicates().values.tolist()
        #print(registered_sit_ids)
        registered_idms = IC_DB["idm"].dropna(how='all').values.tolist()
        # card is detected.
        print(str(datetime.datetime.now()) + " Card is touched.")
        tag = nfc.tag.activate_tt3(clf, target_res)
        #tag.sys = 3
        visitor_idm = binascii.hexlify(tag.idm)
        print(str(datetime.datetime.now()) + " Visitor IDM:"  + visitor_idm)
        #print('  ' + '\n  '.join(tag.dump()))
        # Searching ID from the IDM database
        for registered_idm in registered_idms:
          if registered_idm in visitor_idm:
            registered_flag = True
            propaty_regisuter = IC_DB[IC_DB["idm"]==registered_idm]
            #print(propaty_regisuter)
            propaty = list(propaty_regisuter.index.values)
            #print(propaty[0])
            sit_id = propaty[0][0]
            #print(sit_id)
            device = propaty[0][1]
            #print(device)
            if state_of_key:
              state = "LOCK"
            else :
              state = "OPEN"
            print(str(datetime.datetime.now()) + ", state : " + state + ", SIT_ID : " + sit_id + ", type : " + device)
            break

        # Checking the card has system code
        if registered_flag == False:
          if hasattr(tag, 'request_system_code') == True:
            system_codes = tag.request_system_code()
            sc_zero = system_codes[0]
            #print("SYS:" + hex(sc))
            if sys_code_student_card == sc_zero:
              # SIT ID card
              sc = nfc.tag.tt3.ServiceCode(service_code >> 6, service_code & 0x3f)
              bc = nfc.tag.tt3.BlockCode(0, service=0)
              visitor_data = tag.read_without_encryption([sc], [bc])
              #print(visitor_data)
              visitor_sit_id = visitor_data[SIT_ID_CARD_OFFSET:SIT_ID_CARD_OFFSET+SIT_ID_CARD_NUMBER_OF_CHARS]
              print(str(datetime.datetime.now()) + " Visitor SIT ID: "
                + visitor_sit_id)
              for sit_id in registered_sit_ids:
                if sit_id in visitor_sit_id:
                  registered_flag = True
                  device = "SIT_CARD"
                  if state_of_key:
                    state = "LOCK"
                  else :
                    state = "OPEN"
                  print(str(datetime.datetime.now()) + ", state : " + state + ", SIT_ID : " + sit_id + ", type : " + device)
                  break

          if registered_flag == False:
            print("This is unknown IC card 2")

    except Exception as e:
      registered_flag = False
      print("error: %s" % e)
      #print('  ' + '\n  '.join(tag.dump()))

    finally:
      if registered_flag == True:
        self.toggle_key()
      registered_flag = False
      time.sleep(1.0)
      clf.close()

if __name__ == '__main__':
  # standalone or not?
#    members = open("members.dat", "r")
  GPIO.setmode(GPIO.BCM)
  GPIO.setup(GP_OUT, GPIO.OUT)
  try:
    cr = MyCardReader()
    while True:
      print(str(datetime.datetime.now()) + " Polling...")
      cr.read_rfid()
      time.sleep(TIME_WAIT)

  except KeyboardInterrupt:
    print('Exit...')
    GPIO.cleanup()
