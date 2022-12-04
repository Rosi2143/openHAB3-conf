#!/usr/bin/env python3
# # -*- coding: utf-8 -*-

"""implements the handling of tinkerforge base functionality"""


class TinkerforgeBase:
    """handles connections and generic functions for all bricklets"""

    # connection element for bricklet connection
    ipconnection = None

    def __init__(self, ipconnection, logger):
        """base class for all tinkerforge devices"""

        self.ipconnection = ipconnection
        # logger passed via constructor
        self.logger = logger

    def check_device_identity(self, device, expected_name):
        """check if the configured device it identical with the read out device"""
        (uid, connect_id, position, hardware_version,
         firmware_version, device_identifier) = device.get_identity()
        self.logger.info("added device:\n" +
                         "\tUID          : " + uid + "\n" +
                         "\tconnected to : " + connect_id + "\n" +
                         "\tat position  : " + position + "\n" +
                         "\tHW version   : " + ".".join([str(i) for i in hardware_version]) + "\n" +
                         "\tFW version   : " + ".".join([str(i) for i in firmware_version]) + "\n" +
                         "\tdevice ident : " + str(device_identifier))

        if device_identifier != expected_name:
            raise SystemExit("incorrect device configuration - configured: "
                             + BrickletIo16V2.DEVICE_DISPLAY_NAME
                             + " read out: "
                             + str(device_identifier)
                             + " - see also https://www.tinkerforge.com/de/doc/Software/Device_Identifier.html")
