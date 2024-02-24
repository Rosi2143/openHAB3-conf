"""
This script maps the wall switches to the lights they handle.
 change to reload
"""

import logging  # required for extended logging

import HABApp
from HABApp.openhab.items import GroupItem, SwitchItem
from HABApp.core.events import ValueChangeEventFilter
from HABApp.openhab import transformations

logger = logging.getLogger("Switch2Light")

param_file = "switch2light"
LONG_MAP = HABApp.DictParameter(param_file, "Long", default_value="")
SHORT_MAP = HABApp.DictParameter(param_file, "Short", default_value="")
TOGGLE_MAP = transformations.map["toggle.map"]


class Switch2Light(HABApp.Rule):
    """This class handles Hue internal states."""

    def __init__(self):
        """initialize the logger test"""
        super().__init__()

        oh_group_switch_long = GroupItem.get_item("gSchalter_Long")
        for oh_item in oh_group_switch_long.members:
            oh_item.listen_event(
                self.switch2wall_mapping_long, ValueChangeEventFilter(value="CLOSED")
            )

        oh_group_switch_short = GroupItem.get_item("gSchalter_Short")
        for oh_item in oh_group_switch_short.members:
            oh_item.listen_event(
                self.switch2wall_mapping_short, ValueChangeEventFilter(value="CLOSED")
            )

        logger.info("Switch2Light rule initialized")

    def set_light(self, light_item_name, command):
        """
        set the light to the given command

        Args:
            light_item_name (str): the item name
            command (str): the command
        """
        light_item_name = light_item_name + "_State"
        logger.info(
            "setting item %s - action %s",
            light_item_name,
            command,
        )
        if command == "OFF":
            self.openhab.send_command(light_item_name, "OFF")
        if command == "TOGGLE":
            self.openhab.send_command(
                light_item_name,
                TOGGLE_MAP[str(SwitchItem.get_item(light_item_name).get_value())],
            )
        else:
            self.openhab.send_command(
                light_item_name,
                TOGGLE_MAP[str(SwitchItem.get_item(light_item_name).get_value())],
            )

    def switch2wall_mapping_long(self, event):
        """
        handles long presses of wallswitches

        Args:
            event (_type_): long press item
        """
        logger.info("rule fired because of %s", event.name)

        switch_equipment_name = event.name.replace("_Long", "")
        if switch_equipment_name in LONG_MAP:
            light_items = LONG_MAP[switch_equipment_name]
            if not isinstance(light_items, list):
                self.set_light(light_items["id"], light_items["command"])
            else:
                for light_item in light_items:
                    self.set_light(light_item, light_item["command"])
        else:
            logger.warn("event %s does not exist", switch_equipment_name)

    def switch2wall_mapping_short(self, event):
        """
        handles short presses of wallswitches

        Args:
            event (_type_): short press item
        """
        logger.info("rule fired because of %s", event.name)
        switch_equipment_name = event.name.replace("_Short", "")
        if switch_equipment_name in SHORT_MAP:
            light_item = SHORT_MAP[switch_equipment_name]
            self.set_light(light_item, "TOGGLE")
        else:
            logger.warn("event %s does not exist", switch_equipment_name)


Switch2Light()
