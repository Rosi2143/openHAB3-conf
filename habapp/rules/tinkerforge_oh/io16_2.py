#!/usr/bin/env python3
# # -*- coding: utf-8 -*-

import logging, time, datetime, json, sys
import abc

sys.path.append('/etc/openhab/habapp/rules/')
sys.path.append('/usr/lib/python3/dist-packages/')
from tinkerforge.bricklet_io16_v2 import BrickletIO16V2
from tinkerforge_oh.tinkerforge_base import tinkerforge_base
from tinkerforge_oh.oh_base          import oh_base

class io16_2(tinkerforge_base, oh_base, metaclass=abc.ABCMeta):
    """abstracts the handling of io16_v2 bricklets of tinkerforge"""

    ## uid of this device taken from parameter file
    uid = None
    ## port mapping of this device taken from parameter file
    port_mapping = {}
    ## port name mapping of this device taken from OH transform map file
    port_name_mapping = {}
    ## device that is controlled taken from OH transform map file
    port_device_mapping = {}
    ## hold the time of last change for the port
    port_last_change_mapping = {}
    ## map boolean states to switch states
    port_state_state_mapping = {"True": "ON", "False": "OFF"}
    ## map boolean states to contact states
    port_window_state_mapping = {"True": "Open", "False": "Closed"}

    def map_port_to_text(self, port_number):
        """convert the port number to port readable names"""
        return str(self.port_name_mapping[self.port_mapping[str(port_number)]]).rstrip()

    def map_port_to_device(self, port_number):
        """convert the port number to devices that are switched via this port"""
        return str(self.port_device_mapping[self.port_mapping[str(port_number)]]).rstrip()

    def map_value_to_text(self, value):
        """convert the port number to port names"""
        return str(self.port_name_mapping[value]).rstrip()

    @abc.abstractmethod
    def handle_timediff(self, timediff, port, oh_state):
        """abstract method to make decisions based on time differences of state changes"""
        self.logger.info("function 'io16_2::handle_timediff' needs to be overwritten")

    @abc.abstractmethod
    def set_oh_item_state_abs(self, port, item_name, item_state, inverted_state):
        """abstract method to set an OpenHAB state."""
        self.logger.info("function 'io16_2::set_oh_item_state_abs' needs to be overwritten")

    def cb_input_value(self, channel, changed, value):
        """method called by tinkerforge daemon on state changes."""
        start_time = time.time()
        if changed:
            oh_item = self.port_mapping[str(channel)]
            timediff = datetime.datetime.now() - self.port_last_change_mapping[str(channel)]
            self.port_last_change_mapping[str(channel)] = datetime.datetime.now()
            self.logger.info("changes detected for " + BrickletIO16V2.DEVICE_DISPLAY_NAME + " uid: " + self.uid + " at: "  + datetime.datetime.now().strftime("%d.%b %Y %H:%M:%S"))
            self.logger.debug( "Channel  : " + "{0:02d}".format(channel) + " == " + self.map_port_to_text(channel))
            self.logger.debug( "OH-Item  : " + oh_item)
            self.logger.debug("Changed  : " + str(changed))
            self.logger.debug( "Value    : " + str(value) + " == " + self.map_value_to_text(str(value)))
            self.logger.debug( "timediff : " + str(datetime.timedelta(seconds=timediff.seconds)) + ":" + str(timediff.microseconds/1000) + "ms")
            self.set_oh_item_state_abs(channel, oh_item, self.port_state_state_mapping[str(value)], self.port_state_state_mapping[str(not value)])
            self.handle_timediff(timediff, str(channel), self.map_value_to_text(str(value)))
            self.logger.debug( "---------------------------------------------")
        else:
            self.logger.debug(BrickletIO16V2.DEVICE_DISPLAY_NAME + " uid: " + self.uid + ": nothing changed")
        self.logger.debug("--- %s seconds for callback---\n" % (time.time() - start_time))

    def device_setup(self, device, deviceconfig):
        """setup the io16 device"""
        value = device.get_value()
        for port in range(16):
            self.logger.info(" uid: " + self.uid +\
                            " - Channel " + "{0:02d}".format(port) +\
                            " : '" + self.map_port_to_device(port) +\
                            "' == '" + self.map_port_to_text(port) +\
                            "' : state - " + self.port_window_state_mapping[str(value[port])])

            self.port_last_change_mapping[str(port)] = datetime.datetime.now()

            (period, value_has_to_change ) = device.get_input_value_callback_configuration(port)
            self.logger.info("\tperiod: " + str(period) + "ms - has to change = " + str(value_has_to_change) + "\n")

        period = deviceconfig['device_callback_all_config']["period"]
        value_has_to_change = deviceconfig['device_callback_all_config']["value_has_to_change"]
#        self.logger.info("set_all_input_value_callback_configuration: Setting config with " + str(period) + "ms, value_has_to_change = " + str(value_has_to_change))
#        device.set_all_input_value_callback_configuration(\
#            period,\
#            value_has_to_change)

        for port in range(16):
            _period = period
            _value_has_to_change = value_has_to_change
            if "device_callback_config" in deviceconfig:
                if str(port) in deviceconfig['device_callback_config']:
                    _period = deviceconfig['device_callback_config'][str(port)]["period"]
                    _value_has_to_change = deviceconfig['device_callback_config'][str(port)]["value_has_to_change"]
                self.logger.info("set_input_value_callback_configuration: config for port " +\
                                "{0:02d}".format(port) + " with " +\
                                str(_period) + "ms, value_has_to_change = " +\
                                str(_value_has_to_change))
                device.set_input_value_callback_configuration(port,\
                    _period,\
                    _value_has_to_change)
        self.logger.info("---------------------------------------------\n")

    def __init__(self, ipconnection, deviceconfig, OH_port_mapping_file, logger):
        """initiaze the handler of io16 modules"""
        tinkerforge_base.__init__(self, ipconnection, logger)
        oh_base.__init__(self, OH_port_mapping_file, logger)
        self.uid = deviceconfig['uid']
        ## see class definition
        self.port_mapping = deviceconfig['OH_port_mapping']
        ## store the logger passed in constructor
        self.logger = logger

        self.logger.info("initializing bricklet " + BrickletIO16V2.DEVICE_DISPLAY_NAME + " with uid: " + self.uid)

        self.logger.debug("initializing bricklet:")
        self.logger.debug("\t\ttype         : " + BrickletIO16V2.DEVICE_DISPLAY_NAME)
        self.logger.debug("\t\tuid          : " + self.uid)
        self.logger.debug("\t\tmapfile      : " + self.mapfile)
        self.logger.debug("\t\tport_mapping : " + json.dumps(self.port_mapping, indent=2))

        io16 = BrickletIO16V2(self.uid, ipconnection)

        io16.register_callback(io16.CALLBACK_INPUT_VALUE, self.cb_input_value)

        self.check_device_identity(io16, BrickletIO16V2.DEVICE_IDENTIFIER)

        self.read_map_file()

        self.device_setup(io16, deviceconfig)
