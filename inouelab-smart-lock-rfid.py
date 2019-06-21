import RPi.GPIO as GPIO
import datetime
import binascii
import nfc
import ndef
import time

from threading import Thread, Timer

# Database for ID cards of SIT students and professors
registered_sit_ids = [
  # Professors
#  '0215723', # Yoshihiro Niitsu
#  'I026866', # Ryo Yamamoto
#  '0100123', # Takumi Miyoshi
#  '0286898',  # Taku Yamazaki
  #Inouelab Students
  'NB16507',   #Aljehani Maher Saleh H
  'NB16501',   #Worawat Tee LaWanont
  'NB17004',   #Oba sayuko
  'MF17066',   #Muhammad Zulfadhli Bin Ismail
  'MF17501',   #Sunthad Kant
  'MF17502',   #Nuttakarn Kitpo
  'MF17075',   #Ntihemuka Materne
  'BP15013',   #kakeru Ehara
  'BP15026',   #kouki kawase
  'BP15044',   #Tiharu Shiraishi
  'BP15046',   #Taiti Souma
  'BP15080',   #Naoto Maida
  'BP15081',   #Kazuki Makita
  'BP15098',   #Kei Yamagishi
  'BP15109',   #Kentaro Watanabe
  'BP16020',
  'BP16063',
  'BP16073',
  'BP16079',
  'BP16086',
  'BP16087',
  'BP16109'
]

# Database for RFID cards (RFID, felica, etc.)
registered_idms = [
#  '0139c6fdd097e6f5', # iPhone, Taku Yamazaki
#  '010102124717b30f', # RFID card (ICOCA)
  '0134b401ff1803af', #Android, Kazuki Makita
  '01010312c4169523', #RFID card(SUICA), Kazuki Makita
  '01341301bf179b62'  #Android, Taichi Soma
]
  #'0101041071103416', #RFID card(SUICA), Taichi Soma

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
            print(str(datetime.datetime.now()) + " The visitor is registered.")
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
              print(visitor_data)
              print(str(datetime.datetime.now()) + " Visitor SIT ID: "
                + visitor_data[SIT_ID_CARD_OFFSET:SIT_ID_CARD_OFFSET+SIT_ID_CARD_NUMBER_OF_CHARS])
              for sit_id in registered_sit_ids:
                if sit_id in visitor_data[SIT_ID_CARD_OFFSET:SIT_ID_CARD_OFFSET+SIT_ID_CARD_NUMBER_OF_CHARS]:
                  registered_flag = True
                  break

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
