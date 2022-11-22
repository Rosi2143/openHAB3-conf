#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging, sys

sys.path.append('/etc/openhab/habapp/rules/')
from tinkerforge_oh.io16_2 import io16_2

class io16_window(io16_2):
    """specific class for handling of io16 devices for windows"""

    def __init__(self, ipconnection, deviceconfig, OH_port_mapping_file, logger):
        io16_2.__init__(self, ipconnection, deviceconfig, OH_port_mapping_file, logger)
        ## logger passed via constructor
        self.logger = logger

    def handle_timediff(self, timediff, port, oh_state):
        self.logger.debug("function 'io16_window::handle_timediff' ignored for windows")

    def set_oh_item_state_abs(self, port, item_name, item_state, inverted_item_state):
        self.set_oh_item_state(item_name, item_state, "Switch")
