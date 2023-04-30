import datetime
from multiprocessing import Process
import sys, threading
import os
import time
import platform
import serial
from serial.serialutil import Timeout

if platform.system() == "Linux":
    # port = serial.Serial("/dev/ttyserial0", baudrate=115200, timeout=3.0)
    port = serial.Serial("/dev/ttyS0", baudrate=115200, timeout=3.0)
elif platform.system() == "Windows":
    port = serial.Serial("COM15", baudrate=115200, timeout=3.0)
pass

mlevels = []
waterTankLvl = 99
connected = True

def serialRead():
  global connected, mlevels, waterTankLvl
  while connected:
    Data = port.readline()
    Data = str(Data, 'UTF-8')
    if "mlevels" in Data:
        mlevels = Data.split(',')
        # todo uncomment for debug
        # print(f"mLvl1: {mlevels[1]}")
        # print(f"mLvl2: {mlevels[2]}")
        # print(f"mLvl3: {mlevels[3]}")
        # print(f"mLvl4: {mlevels[4]}")
        
    elif "tanklvl" in Data:  
        value = Data.split(',')
        waterTankLvl = value[1]
           
    elif "plant1" in Data:
        print("watering...")   
        port.write(str.encode(f"pump1on#"))
        time.sleep(12)
        port.write(str.encode(f"pump1off#"))
        
    elif "plant2" in Data:
        print("watering...")   
        port.write(str.encode(f"pump2on#"))
        time.sleep(12)
        port.write(str.encode(f"pump2off#"))
        
    elif "plant3" in Data:
        print("watering...")   
        port.write(str.encode(f"pump3on#"))
        time.sleep(12)
        port.write(str.encode(f"pump3off#"))
    else:
        pass


def getWLvl():
    mlevels[1] = int(moistCal(int(mlevels[1]), 250, 566, 100, 0))
    mlevels[2] = int(moistCal(int(mlevels[2]), 243, 567, 100, 0))
    mlevels[3] = int(moistCal(int(mlevels[3]), 245, 565, 100, 0))
    mlevels[4] = int(moistCal(int(mlevels[4]), 240, 570, 100, 0))
    if mlevels[1] > 100:
        updateWLvl()
        time.sleep(.5)
        getWLvl()
    return mlevels

def moistCal (x, in_min, in_max, out_min, out_max):
  return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

def updateWLvl():
    port.write(str.encode(f"msense#"))
    return True

def waterPlant1():
    print("watering1...")   
    port.write(str.encode(f"pump1on#"))
    time.sleep(10)
    port.write(str.encode(f"pump1off#"))
    print("done1...")   
    return True

def waterPlant2():
    print("watering2...")   
    port.write(str.encode(f"pump2on#"))
    time.sleep(10)
    port.write(str.encode(f"pump2off#"))
    print("done2...")   
    return True

def waterPlant3():
    print("watering3...")   
    port.write(str.encode(f"pump3on#"))
    time.sleep(12)
    port.write(str.encode(f"pump3off#"))
    print("done3...")   
    return True

def getTankLvl():
    return waterTankLvl

def updateTankLvl():
    port.write(str.encode(f"tanklvl#"))
    return True

serial = threading.Thread(target=serialRead, args=())
serial.setDaemon(True)
serial.start()