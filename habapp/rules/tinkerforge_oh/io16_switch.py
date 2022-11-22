#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json, sys

sys.path.append('/etc/openhab/habapp/rules/')
from tinkerforge_oh.io16_2 import io16_2

class io16_switch(io16_2):
    """specific class for handling of io16 devices for switches"""

    ## map from parameter file which OH item is controlled
    OH_short_long_mapping = {}

    def __init__(self, ipconnection, deviceconfig, OH_port_mapping_file, logger):
        io16_2.__init__(self, ipconnection, deviceconfig, OH_port_mapping_file, logger)
        ## see element definition
        self.OH_short_long_mapping = deviceconfig['OH_short_long_mapping']
        ## logger passed via constructor
        self.logger = logger

    def handle_timediff(self, timediff, port, oh_state):
        if oh_state == "released":
            press=""
            if timediff.total_seconds() > 2:
                press = "Long"
            else:
                press = "Short"

            OH_itemName = self.OH_short_long_mapping[port] + "_" + press
            self.logger.info(press + " Press detected for " + OH_itemName)
            if self.OH_short_long_mapping[port] != "":
                self.set_oh_item_state(OH_itemName, "CLOSED", "Contact")
            else:
                self.logger.debug("no action defined for press:" + press)
        else:
            self.logger.info("state = " + oh_state)

    def set_oh_item_state_abs(self, port, item_name, item_state, inverted_item_state):
        if "switch_overwrite" in self.OH_short_long_mapping:
            if str(port) in self.OH_short_long_mapping["switch_overwrite"]:
                if self.OH_short_long_mapping["switch_overwrite"][str(port)] == "inverted":
                    self.logger.info("switch overwrite for: " + item_name + ":" + inverted_item_state)
                    self.set_oh_item_state(item_name, inverted_item_state, "Switch")
                else:
                    self.logger.info("switch overwrite for: " + item_name + ":" + item_state)
                    self.set_oh_item_state(item_name, item_state, "Switch ")
            else:
                self.logger.debug("no overwrite(1): " + json.dumps(self.OH_short_long_mapping, indent=2))
        else:
            self.logger.debug("no overwrite(2): " + json.dumps(self.OH_short_long_mapping, indent=2))
