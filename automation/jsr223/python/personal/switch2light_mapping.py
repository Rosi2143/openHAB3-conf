"""
This script maps the wall switches to the lights they handle.
"""

import os
import json
from core.rules import rule
from core.triggers import when

scriptpath = os.environ["OPENHAB_CONF"] + "/automation/jsr223/python/personal/"
with open(os.path.join(scriptpath, 'switch2light_mapping.json'), "rt") as json_file:
    json_config = json.load(json_file)


@rule("Switch2Light (Long) mapper",
      description="switch light(s) on/off if wall switches are pressed long",
      tags=["wallswitch", "light", "long", "memberchange"])
@when("Member of gSchalter_Long changed to CLOSED")
def switch2wall_mapping_long(event):
    """
    handles long presses of wallswitches

    Args:
        event (_type_): _description_
    """
    switch2wall_mapping_long.log.info(
        "rule fired because of %s", event.itemName)

    switch_equipment_name = event.itemName.replace("_Long", "")
    if switch_equipment_name in json_config["Long"]:
        light_item_name = json_config["Short"][switch_equipment_name] + "_State"
        switch2wall_mapping_long.log.info(
            "setting item %s", light_item_name)
        events.sendCommand(light_item_name, "OFF")
    else:
        switch2wall_mapping_short.log.warn(
            "event %s does not exist", switch_equipment_name)


@rule("Switch2Light (Short) mapper",
      description="switch light(s) on/off if wall switches are pressed short",
      tags=["wallswitch", "light", "short"])
@when("Member of gSchalter_Short changed to CLOSED")
@when("Item Tinkerforge_TestIn_OpenState changed")
def switch2wall_mapping_short(event):
    """
    handles short presses of wallswitches

    Args:
        event (_type_): _description_
    """
    switch2wall_mapping_short.log.info(
        "rule fired because of %s", event.itemName)

    switch_equipment_name = event.itemName.replace("_Short", "")
    if switch_equipment_name in json_config["Short"]:
        light_item_name = json_config["Short"][switch_equipment_name] + "_State"
        switch2wall_mapping_short.log.info(
            "setting item %s", light_item_name)
        if items[light_item_name] == ON:
            events.sendCommand(light_item_name, "OFF")
        else:
            events.sendCommand(light_item_name, "ON")
    else:
        switch2wall_mapping_short.log.warn(
            "event %s does not exist", switch_equipment_name)
