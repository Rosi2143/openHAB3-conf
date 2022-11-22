#!/usr/bin/env python3
# # -*- coding: utf-8 -*-

import json, sys

sys.path.append('/etc/openhab/habapp/rules/')
from tinkerforge.bricklet_industrial_digital_out_4 import BrickletIndustrialDigitalOut4
from HABApp.openhab.events import ItemStateEvent
from HABApp.openhab.items import SwitchItem
from tinkerforge_oh.tinkerforge_base import tinkerforge_base
from tinkerforge_oh.oh_base          import oh_base

class out4(tinkerforge_base, oh_base):
   """abstracts the handling of out4 bricklets of tinkerforge"""

   ## map boolean states to switch states
   port_state_state_mapping = {"True": "ON", "False": "OFF"}

   ## uid read from parameter file
   uid = None
   ## bricklet element
   out4 = None
   ## map port number to name
   port_mapping = {}
   ## logger passed via constructor
   logger = None

   def __init__(self, ipconnection, deviceconfig, logger):
      """initialize the output bricklet"""
      
      tinkerforge_base.__init__(self, ipconnection, logger)
      oh_base.__init__(self, None, logger)

      self.uid = deviceconfig['uid']
      ## see class definition
      self.port_mapping = deviceconfig['OH_port_mapping']
      ## logger passed via constructor
      self.logger = logger

      self.logger.info("initializing bricklet " + BrickletIndustrialDigitalOut4.DEVICE_DISPLAY_NAME + " with uid: " + self.uid)

      self.logger.debug("initializing bricklet:")
      self.logger.debug("\t\ttype         : " + BrickletIndustrialDigitalOut4.DEVICE_DISPLAY_NAME)
      self.logger.debug("\t\tuid          : " + self.uid)
      self.logger.debug("\t\tport_mapping : " + json.dumps(self.port_mapping, indent=2))

      self.out4 = BrickletIndustrialDigitalOut4(self.uid, ipconnection)

      self.check_device_identity(self.out4, BrickletIndustrialDigitalOut4.DEVICE_IDENTIFIER)

      self.check_ports()

      self.add_item_listener()
#      self.run_every(10, 60, self.check_ports)

   # taken from https://realpython.com/python-bitwise-operators/#getting-a-bit
   def get_bit(self, value, bit_index):
      """get a bitmask with only the selected bit (not)set"""

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

   def check_ports(self):
      """get port value from bricklet"""

      self.logger.info( f"check_ports for {self.uid}")
      portvalue = self.out4.get_value()
      for portNumber, oh_item in self.port_mapping.items():
         if self.get_normalized_bit(portvalue, int(portNumber)):
            self.logger.info("Bit " + portNumber + " is set -- " + oh_item)
         else:
            self.logger.info("Bit " + portNumber + " is not set" + oh_item)

   def add_item_listener(self):
      """add listener to all openHAB items"""

      self.logger.info( f"add listener for items: {self.uid}")
      for oh_item in self.port_mapping.values():
         if self.openhab.item_exists(oh_item):
               switchItem = SwitchItem.get_item(oh_item)
               switchItem.listen_event(self.switchitem_update, ItemStateEvent)
         else:
               self.logger.error(f"{oh_item} does not exist")

   def switchitem_update(self, event):
      """listener handler"""

      assert isinstance(event, ItemStateEvent)
      self.logger.info(f'received {event.name} <- {event.value}')
      portNumber = list(self.port_mapping.keys())[list(self.port_mapping.values()).index(event.name)]
      selectionMask = 0
      selectionMask = self.set_bit(selectionMask, int(portNumber))
      if event.value == "ON":
         self.logger.debug( f"{self.uid}: setting port {portNumber} to {event.value} : Mask = {selectionMask}")
         self.out4.set_selected_values(selectionMask, selectionMask)
      else:
         self.logger.debug( f"{self.uid}: clearing port {portNumber} : Mask = {selectionMask}")
         self.out4.set_selected_values(selectionMask, 0)
