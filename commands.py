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
from multiprocessing import Process

from general import getWLvl, updateWLvl, waterPlant1, waterPlant2, waterPlant3


comFree = True
debug = False

def runCommand(command):
    global comFree, debug
################################################# COMMANDS ######################################

    if command == 'plant1' and comFree == True:
        comFree = False
        comFree = waterPlant1()
        if debug:
            print(f"{command}: {comFree}")
            
    elif command == 'plant2' and comFree == True:
        comFree = False
        comFree = waterPlant2()
        if debug:
            print(f"{command}: {comFree}")
            
    elif command == 'plant3' and comFree == True:
        comFree = False
        comFree = waterPlant3()
        if debug:
            print(f"{command}: {comFree}")
            


def run_command(com):
    commandThread = Process(target=runCommand, args=(com,))
    commandThread.start()

