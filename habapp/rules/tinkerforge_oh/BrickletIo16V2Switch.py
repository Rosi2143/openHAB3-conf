#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import sys
import logging  # required for extended logging

sys.path.append('/etc/openhab/habapp/rules/')
from tinkerforge_oh.BrickletIo16V2 import BrickletIo16V2


class BrickletIo16V2Switch(BrickletIo16V2):
    """specific class for handling of io16 devices for switches"""

    def __init__(self, ipconnection, deviceconfig, logger):
        BrickletIo16V2.__init__(self, ipconnection, deviceconfig, logger)
        # logger passed via constructor
        self.logger = logger

        for port in range(self.CONST_NUMBER_OF_PINS):
            for extention in ["_Short", "_Long"]:
                oh_item_name = self.port_mapping[str(port)] + extention
                self.logger.debug(
                    "Set default value of %s to OPEN", oh_item_name)
                self.set_oh_item_state(oh_item_name, "OPEN", "Contact")

    def handle_timediff(self, timediff, port, oh_state):
        """check if the time was 'Short' or 'Long'"""
        contact_state_map = {"True": "pressed", "False": "released"}
        if contact_state_map[oh_state] == "released":
            press = ""
            if timediff.total_seconds() > 2:
                press = "Long"
            else:
                press = "Short"

            oh_item_name = self.port_mapping[port] + "_" + press
            self.logger.info(press + " Press detected for " + oh_item_name + "(" + str(timediff.total_seconds()) + ")ms")
            if self.port_mapping[port] != "":
                self.set_oh_item_state(oh_item_name, "CLOSED", "Contact")
            else:
                self.logger.debug("no action defined for press:" + press)
        else:
            self.logger.info("state = " + oh_state)

    def set_oh_item_state_abs(self, port, item_name, item_state, inverted_item_state):
        """ abstract method to set the state of a switch item"""

        if "switch_overwrite" in self.port_mapping:
            if str(port) in self.port_mapping["switch_overwrite"]:
                if self.port_mapping["switch_overwrite"][str(port)] == "inverted":
                    item_name = item_name + "_OpenState"
                    self.logger.info("switch overwrite for: " +
                                     item_name + ":" + inverted_item_state)
                    self.set_oh_item_state(
                        item_name, inverted_item_state, "Contact")
                else:
                    self.logger.info("switch overwrite for: " +
                                     item_name + ":" + item_state)
                    self.set_oh_item_state(item_name, item_state, "Contact ")
            else:
                self.logger.debug("no overwrite(1): " +
                                  json.dumps(self.port_mapping, indent=2))
        else:
            self.logger.debug("no overwrite(2): " +
                              json.dumps(self.port_mapping, indent=2))
