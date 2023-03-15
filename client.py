import websocket
import socket
import json
import threading
import sys
import time
import sched
from datetime import datetime
from datetime import timedelta
import os
import json
from pathlib import Path
import platform
from colorama import Fore, Back, Style

from commands import run_command
from general import getWLvl, updateWLvl, updateTankLvl, getTankLvl

connected = True
name = ''


hour, minute = 16, 30
sunSet2_Offset = 20

tankLvl = 99
current_mLvls = []

plant1lvl = 40
plant1lv2 = 40
plant1lv3 = 60



ctrlr_status = False
current_weather = "clear"
current_datetime = datetime.now()
status_update_time = current_datetime
next_water_time_1 = current_datetime
next_water_time_2 = current_datetime
next_water_time_3 = current_datetime
current_day = current_datetime - timedelta(days=1)
sunset_time = current_datetime.replace(hour=hour, minute=minute)
sunset_time_2 =current_datetime.replace(hour=hour, minute=minute+sunSet2_Offset)



def send_msg(mssg, dest):
    global wsapp
    msg = {'message': mssg,
           'username': name,
           'destination': dest}
    jmsg = json.dumps(msg)
    wsapp.send(jmsg)
    # print(f"Sent: {msg}")


def on_open(wsapp):
    print(f"Connected as: {name} @ {time.ctime()}")
    inputThead = threading.Thread(target=useInput, args=())
    inputThead.setDaemon(True)
    inputThead.start()
    
    newDayThead = threading.Thread(target=check_new_day, args=())
    newDayThead.setDaemon(True)
    newDayThead.start()

    treeThead = threading.Thread(target=plant_controller, args=())
    treeThead.setDaemon(True)
    treeThead.start()
    
    plantsThead = threading.Thread(target=check_plants, args=())
    plantsThead.setDaemon(True)
    plantsThead.start()
    
    updateWLvl() 
    updateTankLvl()
    
    time.sleep(.25)
    send_msg(f"mLevels:{str(getWLvl())}", 'web')
    time.sleep(.5)
    send_msg(f"TankLvl:{str(getTankLvl())}", 'web')
    time.sleep(.5)
    send_msg(f"ip: {get_ip()}", 'web')


def on_close(wsapp, close_status_code, close_msg):
    global connected
    print('disconnected from server')
    if connected:
        print("Retry : %s" % time.ctime())
        time.sleep(10)
        __create_ws()  # retry per 10 seconds


def on_error(wsapp, error):
    print(error)


def on_message(wsapp, message):
    global current_weather, name, hour, minute
    global sunSet2_Offset, sunset_time, sunset_time_2
    global connected, ctrlr_status
    
    msg = json.loads(message)
    if msg['destination'] == name or msg['destination'] == "all":
        print(f"Rec: {message}")
        print("enter DEST (q to close): ")
        
        if"sunset" in msg['message']:
            sunset = msg['message'].split(':')
            hour = (int(sunset[1]) - 6)+12
            minute = int(sunset[2])
            current_time = datetime.now()
            #todo minute + sunset2_offet could be greater than 59
            sunset_time = current_time.replace(hour=hour, minute=minute)
            sunset_time_2 = current_time.replace(hour=hour, minute=minute+sunSet2_Offset)
            print(f"Sunset Time Updated => hour: {hour} : minute: {minute}")
            print("enter DEST (q to close): ")
            
        elif"getlvl" in msg['message']:
            updateWLvl() 
            time.sleep(.25) 
            send_msg(f"waterLvl:{str(getWLvl())}", 'web')
        
        elif msg['message'] == "auto":
            ctrlr_status = True
            send_msg(f"ctrlr_status:{str(ctrlr_status)}", 'web')
            
        elif msg['message'] == "autooff":
            ctrlr_status = False
            send_msg(f"ctrlr_status:{str(ctrlr_status)}", 'web')

        elif msg['message'] == "status":
            updateTankLvl()
            time.sleep(.25) 
            updateWLvl()
            time.sleep(.25) 
            send_msg(f"mLevels:{str(getWLvl())}", msg['username'])
            time.sleep(.5)
            send_msg(f"TankLvl:{str(getTankLvl())}", msg['username'])
            time.sleep(.5)
            send_msg(f"ctrlr:{str(ctrlr_status)}", msg['username'])
            time.sleep(.5)
            send_msg(f"ip: {get_ip()}", msg['username'])

            
        elif msg['message'] == "exit":
            send_msg("Disconecting...", 'web')
            run_command('moff')
            time.sleep(10)
            connected = False
            print("Disconecting...")
            send_msg("close", name)
            time.sleep(1)
            wsapp.close()
            print("Closing...")
            
        elif msg['message'] == "shutdown":
            send_msg("Shutting Down...", 'web')
            run_command('moff')
            time.sleep(10)
            connected = False
            print("Disconecting...")
            send_msg("close", name)
            time.sleep(1)
            wsapp.close()
            print("Closing...")
            os.system("sudo shutdown now")
            
        elif msg['message'] == "reboot":
            send_msg("Rebooting Now...", 'web')
            run_command('moff')
            time.sleep(10)
            connected = False
            print("Disconecting...")
            send_msg("close", name)
            time.sleep(1)
            wsapp.close()
            print("Closing...")
            os.system("sudo reboot now")


        else:
            print(f"msg: {msg['message']}")
            print("enter DEST (q to close): ")
            run_command(msg['message'])


def __create_ws():
    global wsapp
    global connected
    while connected:
        try:
            websocket.enableTrace(False)
            wsapp = websocket.WebSocketApp("ws://synapse.viewdns.net:8000/ws/term/?",
                                           header={
                                               "username": name,
                                               "message": "connected",
                                               "destination": " "
                                           },
                                           on_message=on_message,
                                           on_error=on_error,
                                           on_close=on_close,
                                           )
            wsapp.on_open = on_open
            wsapp.run_forever(
                skip_utf8_validation=True, ping_interval=10, ping_timeout=8)
        except Exception as e:
            print("Websocket connection Error  : {0}".format(e))
        if connected:
            print("Reconnecting websocket  after 10 sec")
            time.sleep(10)


f = Path('name.json')
if f.is_file():
    f = open('name.json')
    data = json.load(f)
    name = data['client']['deviceName']
else:
    val = input("Enter Client Device Name: ")
    data = {"client": {"deviceName": val}}
    with open('name.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    name = name = data['client']['deviceName']
    f.close()
    # todo figure out why the client needs to be restarted when name is assigned
#########################################################################


#########################################################################
def check_plants():    # runs in thread
    global connected, current_datetime, status_update_time
    time.sleep(15)
    print("Moister checker running...")
    while connected:
        current_datetime = datetime.now()
        if current_datetime > status_update_time:
            updateWLvl() 
            updateTankLvl()
            time.sleep(.25) 
            send_msg(f"MoistLvl:{str(getWLvl())}", 'reddb')
            send_msg(f"TankLvl:{str(getTankLvl())}", 'reddb')
            tankLvl = getTankLvl()
            current_mLvls = getWLvl()
            status_update_time = status_update_time + timedelta(minutes=5)
        time.sleep(10)
        
#####################################################################


def check_new_day():  # runs in thread
    global connected, name
    global  current_day
    time.sleep(5)
    print("New Day Updater Running...")
    while connected:
        if current_day.day != datetime.now().day:
            current_day = datetime.now()
            send_msg("sunset", "all")
        time.sleep(90)
        
########################################################################

def plant_controller(): # runs in thread
    global ctrlr_status, connected, current_datetime
    global next_water_time_1, next_water_time_2, next_water_time_3
    global tankLvl, current_mLvls
    global plant1lvl, plant1lv2, plant1lv3
    print("Plant controller running...")
    time.sleep(20) 
    while connected:
        if ctrlr_status:
            current_datetime = datetime.now()
            if tankLvl < 3:
                if current_mLvls[1] < plant1lvl and current_datetime > next_water_time_1:
                    run_command('plant1')
                    next_water_time_1 = datetime.now() + timedelta(hours=6)
                if current_mLvls[2] < plant2lvl and current_datetime > next_water_time_2:
                    run_command('plant2')
                    next_water_time_2 = datetime.now() + timedelta(hours=6)
                if current_mLvls[3] < plant3lvl and current_datetime > next_water_time_3:
                    run_command('plant3')
                    next_water_time_3 = datetime.now() + timedelta(hours=1)
        time.sleep(600)
        
def useInput():
    global connected
    time.sleep(2)
    dest = ""
    send_msg("connected", dest)
    while connected:
        dest = input("enter DEST (q to close): ")
        if dest == 'q':
            connected = False
            print("Disconecting...")
            send_msg("close", dest)
            time.sleep(1)
            wsapp.close()
            print("Closing...")
        else:
            smsg = input("enter msg (q to close): ")
            if smsg == 'q':
                connected = False
                print("Disconecting...")
                send_msg("close", dest)
                time.sleep(1)
                wsapp.close()
                print("Closing...")
            else:
                send_msg(smsg, dest)
                time.sleep(.3)
                
def get_ip():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0)
        try:
            # doesn't even have to be reachable
            s.connect(('10.254.254.254', 1))
            IP = s.getsockname()[0]
        except Exception:
            IP = '127.0.0.1'
        finally:
            s.close()
        return IP


if __name__ == "__main__":
    try:
        __create_ws()
    except Exception as err:
        print(err)
        print("connect failed")
