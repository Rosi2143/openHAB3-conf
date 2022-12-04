#!/usr/bin/env python3
# # -*- coding: utf-8 -*-

"""implements the handling of tinkerforge bricklet io16_v2"""

import time
import datetime
import json
import sys
import abc
import logging  # required for extended logging

sys.path.append('/usr/lib/python3/dist-packages')
from tinkerforge.bricklet_io16_v2 import BrickletIO16V2

sys.path.append('/etc/openhab/habapp/rules/')
from tinkerforge_oh.OhBase import OhBase
from tinkerforge_oh.TinkerforgeBase import TinkerforgeBase


class BrickletIo16V2(TinkerforgeBase, OhBase, metaclass=abc.ABCMeta):
    """abstracts the handling of io16_v2 bricklets of tinkerforge"""

    CONST_NUMBER_OF_PINS = 16
    # uid of this device taken from parameter file
    uid = None
    # port mapping of this device taken from parameter file
    port_mapping = {}
    # hold the time of last change for the port
    port_last_change_mapping = {}
    # map boolean states to switch states
    port_state_state_mapping = {"True": "OPEN", "False": "CLOSED"}

    def map_port_to_device(self, port_number):
        """convert the port number to devices that are switched via this port"""
        return str(self.port_mapping[str(port_number)]).rstrip()

    @abc.abstractmethod
    def handle_timediff(self, timediff, port, oh_state):
        """abstract method to make decisions based on time differences of state changes"""
        self.logger.info(
            "function 'BrickletIo16V2::handle_timediff' needs to be overwritten")

    @abc.abstractmethod
    def set_oh_item_state_abs(self, port, item_name, item_state, inverted_item_state):
        """abstract method to set an openHAB state."""
        self.logger.info(
            "function 'BrickletIo16V2::set_oh_item_state_abs' needs to be overwritten")

    def cb_input_value(self, channel, changed, value):
        """method called by tinkerforge daemon on state changes."""
        start_time = time.time()
        if changed:
            oh_item = self.map_port_to_device(channel)
            timediff = datetime.datetime.now(
            ) - self.port_last_change_mapping[str(channel)]
            self.port_last_change_mapping[str(
                channel)] = datetime.datetime.now()
            self.logger.info("changes detected for %s uid: %s at: %s", BrickletIO16V2.DEVICE_DISPLAY_NAME,
                             self.uid, datetime.datetime.now().strftime("%d.%b %Y %H:%M:%S"))
            self.logger.debug(
                "Channel   : %02d == %s", channel, self.map_port_to_device(channel))
            self.logger.debug("OH-Item   : %s", oh_item)
            self.logger.debug("Changed   : %s", str(changed))
            self.logger.debug("New Value : %s", str(value))
            self.logger.debug("timediff  : %s : %sms", str(datetime.timedelta(
                seconds=timediff.seconds)), str(timediff.microseconds / 1000))
            self.set_oh_item_state_abs(channel, oh_item, self.port_state_state_mapping[str(
                value)], self.port_state_state_mapping[str(not value)])
            self.handle_timediff(timediff, str(channel), oh_item)
            self.logger.debug("---------------------------------------------")
        else:
            self.logger.debug(BrickletIO16V2.DEVICE_DISPLAY_NAME +
                              " uid: " + self.uid + ": nothing changed")
        self.logger.debug("--- %s seconds for callback---\n" %
                          (time.time() - start_time))

    def device_setup(self, device, deviceconfig):
        """setup the io16 device"""
        value = device.get_value()
        for port in range(self.CONST_NUMBER_OF_PINS):
            current_state = self.port_state_state_mapping[str(value[port])]
            self.logger.info(" uid: " + self.uid +
                             " - Channel " + "{0:02d}".format(port) +
                             " : '" + self.map_port_to_device(port) +
                             "' : state - " + current_state)

            self.port_last_change_mapping[str(port)] = datetime.datetime.now()

            (period, value_has_to_change) = device.get_input_value_callback_configuration(port)
            self.logger.info("\tperiod: " + str(period) +
                             "ms - has to change = " + str(value_has_to_change) + "\n")

            self.cb_input_value(port, True, value[port])

        period = deviceconfig['device_callback_all_config']["period"]
        value_has_to_change = deviceconfig['device_callback_all_config']["value_has_to_change"]

        for port in range(self.CONST_NUMBER_OF_PINS):
            _period = period
            _value_has_to_change = value_has_to_change
            if "device_callback_config" in deviceconfig:
                if str(port) in deviceconfig['device_callback_config']:
                    _period = deviceconfig['device_callback_config'][str(
                        port)]["period"]
                    _value_has_to_change = deviceconfig['device_callback_config'][str(
                        port)]["value_has_to_change"]
                self.logger.info("set_input_value_callback_configuration: config for port " +
                                 "{0:02d}".format(port) + " with " +
                                 str(_period) + "ms, value_has_to_change = " +
                                 str(_value_has_to_change))
                device.set_input_value_callback_configuration(port,
                                                              _period,
                                                              _value_has_to_change)
        self.logger.info("---------------------------------------------\n")

    def __init__(self, ipconnection, deviceconfig, logger):
        """initialise the handler of io16 modules"""
        TinkerforgeBase.__init__(self, ipconnection, logger)
        OhBase.__init__(self, logger)
        self.uid = deviceconfig['uid']
        # see class definition
        self.port_mapping = deviceconfig['OH_port_mapping']
        # store the logger passed in constructor
        self.logger = logger

        self.logger.info("initializing bricklet " +
                         BrickletIO16V2.DEVICE_DISPLAY_NAME + " with uid: " + self.uid)

        self.logger.debug("initializing bricklet:")
        self.logger.debug("\t\ttype         : " +
                          BrickletIO16V2.DEVICE_DISPLAY_NAME)
        self.logger.debug("\t\tuid          : " + self.uid)
        self.logger.debug("\t\tport_mapping : " +
                          json.dumps(self.port_mapping, indent=2))

        io16_bricklet = BrickletIO16V2(self.uid, ipconnection)

        io16_bricklet.register_callback(
            io16_bricklet.CALLBACK_INPUT_VALUE, self.cb_input_value)

        self.check_device_identity(
            io16_bricklet, BrickletIO16V2.DEVICE_IDENTIFIER)

        self.device_setup(io16_bricklet, deviceconfig)
