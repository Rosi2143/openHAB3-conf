#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import datetime
import logging  # required for extended logging

import HABApp
from HABApp.openhab.items import ContactItem, SwitchItem


class OhBase(HABApp.Rule):
    """abstracts the handling of openHAB interaction"""

    def __init__(self, logger):
        """initialize the base class and store the OH map file"""
        super().__init__()
        # lagger passed via constructor
        self.logger = logger

    def set_oh_item_state(self, item_name, item_state, item_type):
        """set the state of a OpenHAB item.

        Supported are
        * switch
        * contact"""

        start_time = time.time()
        oh_item = None
        if not self.openhab.item_exists(item_name):
            self.logger.error("Item %s does not exist", item_name)
            return
        else:
            if item_type == "Switch":
                oh_item = SwitchItem.get_item(item_name)
            else:
                if item_type == "Contact":
                    oh_item = ContactItem.get_item(item_name)
                else:
                    self.logger.error("Unknown type: %s", item_type)
                    return
            oh_item.oh_post_update(item_state)
        time_difference = time.time() - start_time
        self.logger.debug(
            f"--- {time_difference:5f} seconds to set state {item_name}({item_type}) ---")

    def run_every(self, startTime, intervalTime, callbackFunction):
        """support cyclic tasks"""
        ret = self.run.every(
            start_time=datetime.timedelta(seconds=startTime),
            interval=datetime.timedelta(seconds=intervalTime),
            callback=callbackFunction
        )
        self.logger.info(
            f"{startTime} : {intervalTime} : {callbackFunction} :: {ret}")

    def test(self):
        """test function

        just log something to see if the function was called"""
        self.logger.info("Hallo")
