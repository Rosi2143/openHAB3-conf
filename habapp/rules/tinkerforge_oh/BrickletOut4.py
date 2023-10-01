#!/usr/bin/env python3
# # -*- coding: utf-8 -*-

"""implements the handling of tinkerforge bricklet BrickletOut4-Industrial"""

import json
import sys
import logging  # required for extended logging

sys.path.append("/usr/lib/python3/dist-packages")
from tinkerforge.bricklet_industrial_digital_out_4 import BrickletIndustrialDigitalOut4

sys.path.append("/etc/openhab/habapp/rules/")
from HABApp.openhab.events import ItemStateUpdatedEvent, ItemStateUpdatedEventFilter
from HABApp.openhab.items import SwitchItem
from tinkerforge_oh.TinkerforgeBase import TinkerforgeBase
from tinkerforge_oh.OhBase import OhBase


class BrickletOut4(TinkerforgeBase, OhBase):
    """abstracts the handling of BrickletOut4 bricklets of tinkerforge"""

    # map boolean states to switch states
    port_state_state_mapping = {"True": "ON", "False": "OFF"}

    def __init__(self, ipconnection, deviceconfig, logger):
        """initialize the output bricklet"""

        TinkerforgeBase.__init__(self, ipconnection, logger)
        OhBase.__init__(self, logger)

        self.state_high = 1
        self.state_low = 0

        # uid read from parameter file
        self.uid = deviceconfig["uid"]
        # map port number to name
        self.port_mapping = deviceconfig["OH_port_mapping"]
        # logger passed via constructor
        self.logger = logger

        # state_map --> to alstate_low filtering out changes only
        self.state_map = {
            0: self.state_low,
            1: self.state_low,
            2: self.state_low,
            3: self.state_low,
        }

        self.logger.info(
            "initializing bricklet "
            + BrickletIndustrialDigitalOut4.DEVICE_DISPLAY_NAME
            + " with uid: "
            + self.uid
        )

        self.logger.debug("initializing bricklet:")
        self.logger.debug(
            "\t\ttype         : " + BrickletIndustrialDigitalOut4.DEVICE_DISPLAY_NAME
        )
        self.logger.debug("\t\tuid          : " + self.uid)
        self.logger.debug(
            "\t\tport_mapping : " + json.dumps(self.port_mapping, indent=2)
        )

        self.out4_bricklet = BrickletIndustrialDigitalOut4(self.uid, ipconnection)

        self.check_device_identity(
            self.out4_bricklet, BrickletIndustrialDigitalOut4.DEVICE_IDENTIFIER
        )

        self.check_ports(True)

        self.add_item_listener()

    def get_bit(self, value, bit_index):
        """taken from https://realpython.com/python-bitwise-operators/#getting-a-bit
        get a bitmask with only the selected bit (not)set"""

        return value & (1 << int(bit_index))

    def get_normalized_bit(self, value, bit_index):
        """get a bit (true/false)"""

        return (value >> int(bit_index)) & 1

    def set_bit(self, value, bit_index):
        """set a bit in element"""

        return value | (1 << int(bit_index))

    def clear_bit(self, value, bit_index):
        """clear a bit in element"""

        return value & ~(1 << int(bit_index))

    def toggle_bit(self, value, bit_index):
        """toggle a bit in element"""

        return value ^ (1 << int(bit_index))

    def check_ports(self, initial_check=False):
        """get port value from bricklet"""

        if not initial_check:
            self.logger.debug("check_ports for %s", self.uid)
        portvalue = self.out4_bricklet.get_value()
        self.logger.debug("portvalue " + str(portvalue))
        self.logger.debug(f"self.state_map = {str(self.state_map)}")
        for port_number, oh_item in self.port_mapping.items():
            self.logger.debug("port_number " + str(port_number))
            self.logger.debug("oh_item    " + oh_item)
            if oh_item == "":
                continue
            oh_item_name = oh_item + "_State"
            is_on = self.get_normalized_bit(portvalue, int(port_number))
            self.logger.debug("is_on " + str(is_on))
            self.logger.debug("state_map " + str(self.state_map[int(port_number)]))
            if (is_on != self.state_map[int(port_number)]) | initial_check:
                self.state_map[int(port_number)] = is_on
                if is_on:
                    self.logger.info(
                        "Bit " + port_number + " is set     -- " + oh_item_name
                    )
                else:
                    self.logger.info(
                        "Bit " + port_number + " is not set -- " + oh_item_name
                    )
                if self.openhab.item_exists(oh_item_name):
                    switch_item = SwitchItem.get_item(oh_item_name)
                    if is_on:
                        switch_item.on()
                    else:
                        switch_item.off()

    def add_item_listener(self):
        """add listener to all openHAB items"""

        self.logger.info(f"add listener for items: {self.uid}")
        for oh_item in self.port_mapping.values():
            if oh_item == "":
                continue
            oh_item_name = oh_item + "_State"
            if self.openhab.item_exists(oh_item_name):
                switch_item = SwitchItem.get_item(oh_item_name)
                switch_item.listen_event(
                    self.switchitem_update, ItemStateUpdatedEventFilter()
                )
            else:
                self.logger.error("%s does not exist", oh_item_name)

    def switchitem_update(self, event):
        """listener handler"""

        assert isinstance(event, ItemStateUpdatedEvent)
        self.logger.info(f"received {event.name} <- {event.value}")
        switch_name = event.name.replace("_State", "")
        port_number = list(self.port_mapping.keys())[
            list(self.port_mapping.values()).index(switch_name)
        ]
        selection_mask = self.set_bit(0, int(port_number))
        if event.value == "ON":
            self.logger.debug(
                f"{self.uid}: setting port {port_number} to {event.value} \
                    : Mask = {selection_mask}"
            )
            self.out4_bricklet.set_selected_values(selection_mask, selection_mask)
            self.state_map[int(port_number)] = self.state_high
        else:
            self.logger.debug(
                f"{self.uid}: clearing port {port_number} : Mask = {selection_mask}"
            )
            self.out4_bricklet.set_selected_values(selection_mask, 0)
            self.state_map[int(port_number)] = self.state_low
        self.logger.debug(f"self.state_map = {str(self.state_map)}")
