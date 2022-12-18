"""
This script enables activation of scenes via a switch-item.
"""

import os
import json
from core.rules import rule
from core.triggers import when


@rule("Activate Scenes",
      description="activate a scene when a switch-item turns ON",
      tags=["scenes"])
@when("Member of gSzenen changed to ON")
def activate_scene(event):
    """
    activates the scenes (collection of items)

    Args:
        event (_type_): _description_
    """

    activate_scene.log.info(
        "rule fired because of %s", event.itemName)

    if event.itemName == "sAlleLichterAus":
        activate_scene.log.info(
            "turn all lights OFF")
        events.sendCommand("gLichterHaus", "OFF")
    elif event.itemName == "sTvLicht":
        activate_scene.log.info(
            "activate TV light")
        events.sendCommand("LichtWohnzimmer_State", "OFF")
        events.sendCommand("FernseherLEDStrip_Color_Temperature", "ON")
        HSBgreen = HSBType().fromRGB(50, 255, 50)
        events.sendCommand("FernseherLEDStrip_Farbe", HSBgreen.toString())
    else:
        activate_scene.log.error(
            "unknown item %s", event.itemName)
