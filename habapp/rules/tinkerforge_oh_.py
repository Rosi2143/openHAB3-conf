#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""implements the handling of tinkerforge within openhab"""

import datetime
import json
import logging  # required for extended logging
import os
import sys
import time

sys.path.append('/usr/lib/python3/dist-packages/')
from tinkerforge.ip_connection import IPConnection

sys.path.append('/etc/openhab/habapp/rules/')
from tinkerforge_oh.BrickletIo16V2 import BrickletIo16V2
from tinkerforge_oh.BrickletIo16V2Switch import BrickletIo16V2Switch
from tinkerforge_oh.BrickletIo16V2Window import BrickletIo16V2Window
from tinkerforge_oh.BrickletOut4 import BrickletOut4

log = logging.getLogger('Tinkerforge')

scriptname = os.path.basename(__file__)
scriptpath = os.path.dirname(__file__)

log.info("Started %s \nName = %s", scriptname, __name__)

try:
    with open(os.path.join(scriptpath, 'tinkerforge_oh.json'), "rt") as json_file:
        json_config = json.load(json_file)

    log.info("\n\n")
    log.info("started at: %s", datetime.datetime.now().strftime(
        "%d.%b %Y %H:%M:%S"))
    log.info("PID = %s", str(os.getpid()))
    log.info("\n")

    ipcon = IPConnection()  # Create IP connection
    ipcon.connect(
        json_config['connection']['host'],
        int(json_config['connection']['port'])
    )  # Connect to brickd

    devices = {}
    for device in json_config['devices']:
        if device['type'] == "BrickletIo16V2":
            new_device = BrickletIo16V2(ipcon, device, log)
        elif device['type'] == "BrickletIo16V2Switch":
            new_device = BrickletIo16V2Switch(ipcon, device, log)
        elif device['type'] == "BrickletIo16V2Window":
            new_device = BrickletIo16V2Window(ipcon, device, log)
        elif device['type'] == "BrickletOut4":
            new_device = BrickletOut4(ipcon, device, log)
        else:
            log.error("unknown type: %s", device["type"])

        devices[device['uid']] = new_device

    log.info("Added %s tinkerforge devices", str(len(devices)))
    if json_config['mode'] == "daemon":
        while (1):
            time.sleep(10)
    else:
        input("Press key to exit\n")  # Use raw_input() in Python 2
    ipcon.disconnect()
finally:
    log.info("\n\nshutdown at: %s \n",
             datetime.datetime.now().strftime("%d.%b %Y %H:%M:%S"))
    logging.shutdown()
