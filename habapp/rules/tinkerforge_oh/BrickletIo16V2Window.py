#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import logging  # required for extended logging

sys.path.append('/etc/openhab/habapp/rules/')
from tinkerforge_oh.BrickletIo16V2 import BrickletIo16V2


class BrickletIo16V2Window(BrickletIo16V2):
    """specific class for handling of io16 devices for windows"""

    def __init__(self, ipconnection, deviceconfig, logger):
        BrickletIo16V2.__init__(self, ipconnection, deviceconfig, logger)
        # logger passed via constructor
        self.logger = logger

    def handle_timediff(self, timediff, port, oh_state):
        """just print a trace that this function is ignored"""
        self.logger.debug(
            "function 'BrickletIo16V2Window::handle_timediff' ignored for windows")

    def set_oh_item_state_abs(self, port, item_name, item_state, inverted_item_state):
        self.set_oh_item_state(item_name + "_OpenState", item_state, "Contact")
