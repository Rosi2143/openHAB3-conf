#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time, json, datetime

import HABApp
from HABApp.openhab.items import ContactItem, SwitchItem

class oh_base(HABApp.Rule):
    """abstracts the handling of openHAB interaction"""

    ## name of the OH transform map file
    mapfile = None

    def __init__(self, OH_port_mapping_file, logger):
        """initialize the base class and store the OH map file"""
        super().__init__()
        self.mapfile = OH_port_mapping_file
        ## lagger passed via constructor
        self.logger = logger

#        self.run_every(20, 70, self.test)

#        self.test()

#        self.run.every(
#            start_time=datetime.timedelta(seconds=10),
#            interval=datetime.timedelta(seconds=20),
#            callback=self.test
#        )

    def set_oh_item_state(self, item_name, item_state, type):
        """set the state of a OpenHAB item.
        
        Supported are 
        * switch
        * contact"""
        start_time = time.time()
        oh_item = None
        if not self.openhab.item_exists(item_name):
            self.logger.error( f"Item " + item_name + " does not exist")
            return
        else:
            if type == "Switch":
                oh_item = SwitchItem.get_item(item_name)
            else:
                if type == "Contact":
                    oh_item = ContactItem.get_item(item_name)
                else:
                    self.logger.error("Unknown type: " + type)
                    return
            oh_item.oh_post_update(item_state)
        time_difference = time.time() - start_time
        self.logger.debug( f"--- {time_difference:5f} seconds to set state {item_name}({type}) ---")

    def read_map_file(self):
        """read the OH map file and store the content in maps"""

        ## @todo - double defined
        self.port_name_mapping = {}
        ## @todo - double defined
        self.port_device_mapping = {}
        if self.mapfile != None:
            with open(self.mapfile) as file:
                for line in file:
                    self.logger.debug("line = " + line.rstrip())
                    line.lstrip().rsplit()
                    if line.startswith("//"):
                        continue
                    if len(line)<=1:
                        continue
                    (key, *map_name) = line.split("=")
                    if len(map_name) != 0:
                        (device, *name) = map_name[0].split(":")
                        if len(name) != 0:
                            self.port_name_mapping[key] = name[0].rstrip()
                            self.port_device_mapping[key] = device.rstrip()
                        else:
                            self.port_name_mapping[key] = map_name[0].rstrip()
                            self.logger.warning("No device->name mapping found for: " + map_name[0].rstrip())
                    else:
                        self.logger.warning("No proper mapping for " + line.rstrip())
                        continue
            self.logger.debug("port_name_mapping = " + json.dumps(self.port_name_mapping, indent=2))
            self.logger.debug("port_device_mapping = " + json.dumps(self.port_device_mapping, indent=2))

    def run_every(self, startTime, intervalTime, callbackFunction):
        """support cyclic tasks"""
        ret = self.run.every(
            start_time=datetime.timedelta(seconds=startTime),
            interval=datetime.timedelta(seconds=intervalTime),
            callback=callbackFunction
        )
        self.logger.info( f"{startTime} : {intervalTime} : {callbackFunction} :: {ret}")

    def test(self):
        """test function 
        
        just log something to see if the function was called"""
        self.logger.info("Hallo")
