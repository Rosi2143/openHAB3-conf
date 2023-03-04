"""
This script maps the wall switches to the lights they handle.
xvs change to reload
"""

import os
import json
from core.rules import rule
from core.triggers import when

scriptpath = os.environ["OPENHAB_CONF"] + "/automation/jsr223/python/personal/"
with open(os.path.join(scriptpath, 'switch2light_mapping.json'), "rt") as json_file:
    json_config = json.load(json_file)


toggle_map = {"ON" : "OFF",
              "OFF" : "ON"
             }


@rule("Switch2Light (Long) mapper",
      description="switch light(s) on/off if wall switches are pressed long",
      tags=["wallswitch", "light", "long", "memberchange"])
@when("Member of gSchalter_Long changed to CLOSED")
def switch2wall_mapping_long(event):
    """
    handles long presses of wallswitches

    Args:
        event (_type_): long press item
    """
    switch2wall_mapping_long.log.info(
        "rule fired because of %s", event.itemName)

    switch_equipment_name = event.itemName.replace("_Long", "")
    if switch_equipment_name in json_config["Long"]:
        light_items = json_config["Long"][switch_equipment_name]
        switch2wall_mapping_short.log.info(
            "found light(s) %s (is type == %s)", light_items, type(light_items))
        if not isinstance(light_items, list):
            switch2wall_mapping_short.log.info(
                "setting item %s", light_items)
            light_item_name = light_items["id"] + "_State"
            if light_items["command"] == "OFF":
                events.sendCommand(light_items, "OFF")
            else:
                events.sendCommand(light_items, toggle_map[str(items[light_item_name])])
        else:
            for light_item in light_items:
                light_item_name = light_item + "_State"
                switch2wall_mapping_short.log.info(
                    "setting item %s", light_item_name)
                if light_item["command"] == "OFF":
                    events.sendCommand(light_item, "OFF")
                else:
                    events.sendCommand(light_item, toggle_map[str(items[light_item_name])])
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
        event (_type_): short press item
    """
    switch2wall_mapping_short.log.info(
        "rule fired because of %s", event.itemName)
    switch_equipment_name = event.itemName.replace("_Short", "")
    if switch_equipment_name in json_config["Short"]:
        light_items = json_config["Short"][switch_equipment_name]
        switch2wall_mapping_short.log.info(
            "found light(s) %s (is type == %s)", light_items, type(light_items))
        if not isinstance(light_items, list):
            switch2wall_mapping_short.log.info(
                "setting item %s", light_items)
            light_item_name = light_items + "_State"
            events.sendCommand(light_items, toggle_map[str(items[light_item_name])])
        else:
            for light_item in light_items:
                light_item_name = light_item + "_State"
                switch2wall_mapping_short.log.info(
                    "setting item %s", light_item_name)
                events.sendCommand(light_item_name, toggle_map[str(items[light_item_name])])
    else:
        switch2wall_mapping_short.log.warn(
            "event %s does not exist", switch_equipment_name)
