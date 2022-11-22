#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import logging, datetime, time, json, os

sys.path.append('/etc/openhab/habapp/rules/')
sys.path.append('/usr/lib/python3/dist-packages/')
from tinkerforge.ip_connection import IPConnection
from tinkerforge_oh.io16_2      import io16_2
from tinkerforge_oh.io16_switch import io16_switch
from tinkerforge_oh.io16_window import io16_window
from tinkerforge_oh.out4        import out4

log = logging.getLogger('Tinkerforge')

scriptname = os.path.basename(__file__)
scriptpath = os.path.dirname(__file__)

log.info("Started " + scriptname + "\nName = " + __name__)

try:
    with open(os.path.join(scriptpath, 'tinkerforge_oh.json')) as json_file:
        json_config = json.load(json_file)

    log.info("\n\n")
    log.info("started at: " + datetime.datetime.now().strftime("%d.%b %Y %H:%M:%S"))
    log.info("PID = " + str(os.getpid()))
    log.info("\n")

    ipcon = IPConnection() # Create IP connection
    ipcon.connect(\
        json_config['connection']['host'],\
        int(json_config['connection']['port'])\
        ) # Connect to brickd

    OH_conf_env_var = ""
    if 'OH_dir_env_path' in json_config['OH_port_mapping']:
        OH_conf_path = OH_conf_env_var = json_config['OH_port_mapping']['OH_dir_env_path']
    else:
        OH_conf_env_var = json_config['OH_port_mapping']['OH_dir_env_var']
        log.debug("use ENV Var " + OH_conf_env_var + "for OH")
        OH_conf_path = os.environ[OH_conf_env_var]
    log.debug("ENV Var " + OH_conf_env_var + "==" + OH_conf_path)
    mapping_file = os.path.join(OH_conf_path,"transform",json_config['OH_port_mapping']['mapfile'])
    log.debug("mapfile = " + mapping_file)

    devices = {}
    for device in json_config['devices']:
        if device['type'] == "io16_2":
            new_device = io16_2(ipcon, device, mapping_file, log)
        elif device['type'] == "io16_switch":
            new_device = io16_switch(ipcon, device, mapping_file, log)
        elif device['type'] == "io16_window":
            new_device = io16_window(ipcon, device, mapping_file, log)
        elif device['type'] == "out4":
            new_device = out4(ipcon, device, log)
        else:
            log.error("unknown type: " + device["type"])

        devices[device['uid']] = new_device

    log.info("Added " + str(len(devices)) + " tinkerforge devices")
    if json_config['mode'] == "daemon":
        while(1):
            time.sleep(10)
    else:
        input("Press key to exit\n") # Use raw_input() in Python 2
    ipcon.disconnect()
finally:
    log.info("\n\nshutdown at: " + datetime.datetime.now().strftime("%d.%b %Y %H:%M:%S") + "\n")
    logging.shutdown()