"""
This script enables activation of scenes via a switch-item.
"""

import logging  # required for extended logging

import HABApp
from HABApp.core.types import HSB
from HABApp.openhab.items import GroupItem
from HABApp.core.events import ValueChangeEventFilter

logger = logging.getLogger("Scenes")


class Scenes(HABApp.Rule):
    """This class handles Hue internal states."""

    def __init__(self):
        """initialize the logger test"""
        super().__init__()

        oh_group_scenes = GroupItem.get_item("gSzenen")
        for oh_item in oh_group_scenes.members:
            oh_item.listen_event(
                self.activate_scene, ValueChangeEventFilter(value="OFF")
            )

        logger.info("Scenes rule initialized")

    def activate_scene(self, event):
        """
        activates the scenes (collection of items)

        Args:
            event (_type_): _description_
        """

        logger.info("rule fired because of %s", event.itemName)

        if event.itemName == "sAlleLichterAus":
            logger.info("turn all lights OFF")
            self.openhab.send_command("gLichterHaus", "OFF")
        elif event.itemName == "sTvLicht":
            logger.info("activate TV light")
            self.openhab.send_command("LichtWohnzimmer_State", "OFF")
            self.openhab.send_command("FernseherLEDStrip_Color_Temperature", "ON")
            HSBgreen = HSB(HSB_value[50], HSB_value[255], HSB_value[50])
            self.openhab.send_command("FernseherLEDStrip_Farbe", HSBgreen.toString())
        else:
            logger.error("unknown item %s", event.itemName)


Scenes()
