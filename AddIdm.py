import paho.mqtt.client as mqtt
import struct
import ast
import json
from ast import literal_eval


MQTT_FILE = "mqtt.txt"
mqtt_broker = open(MQTT_FILE).read()
mqtt_dict = literal_eval(mqtt_broker)
MQTT_BROKER_ADDR = mqtt_dict['MQTT_BROKER_ADDR']
MQTT_BROKER_PORT = mqtt_dict['MQTT_BROKER_PORT']

SUB_TOPIC =  "InouelabSmartHomes/SmartLock/#"
PUB_TOPIC = "InouelabSmartHomes/SmartLock/AddIdm/register"


def onConnect(publisher, user_data, flags, response_code):
    print("response code: {0}".format(response_code))
    publisher.subscribe(SUB_TOPIC, 0)



def onMessage(publisher, user_data, msg):
    print("payload: " + str(msg.payload.decode('utf-8')))


if __name__ == '__main__':    
    mqtt_subscriber = mqtt.Client(protocol=mqtt.MQTTv31)
    mqtt_subscriber.on_connect = onConnect
    mqtt_subscriber.on_message = onMessage
    mqtt_subscriber.connect(host=MQTT_BROKER_ADDR, port=MQTT_BROKER_PORT, keepalive=0)

    mqtt_publisher = mqtt.Client(protocol=mqtt.MQTTv31)
    mqtt_publisher.connect(host=MQTT_BROKER_ADDR, port=MQTT_BROKER_PORT, keepalive=0)

    try:
        mqtt_subscriber.loop_start()
        while(1):
            print('If you want to register IC card, Please follow the instructions')
            student_id = input('Enter your student ID : ')
            IC_type = input('Enter your IC card type : ')
            print("Please check ! student ID : " + student_id + "IC card type : " + IC_type )
            while(1):
                yesno = input('no mistake ? yes or no :')
                if yesno == "yes" or yesno == "no":
                    break        
            if yesno == "yes":
                break
        
        PUB_message = '{"student_id":"' + student_id + '","type":"' + IC_type + '"}'
        mqtt_publisher.publish(PUB_TOPIC, PUB_message, qos=0)

    except KeyboardInterrupt:
        None




    






