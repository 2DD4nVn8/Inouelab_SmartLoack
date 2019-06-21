import csv

filename = "/home/pi/WorkSpace/SmartLock/Inouelab_RFID_DB.csv"
#filename = "Inouelab_RFID_DB.csv"
f = open(filename, mode='w')
header_list = ["student_id","type","idm"]
writer = csv.writer(f, lineterminator='\n')

writer.writerow(header_list)

f.close()

