"""
This script handles mqtt items.
"""

import logging  # required for extended logging

import HABApp
from HABApp.openhab.items import SwitchItem, GroupItem
from HABApp.core.events import ValueChangeEventFilter
from HABApp.openhab import transformations

logger = logging.getLogger("Mqtt")

TOGGLE_MAP = transformations.map["toggle.map"]


class Mqtt(HABApp.Rule):
    """This class handles Hue internal states."""

    def __init__(self):
        """initialize the logger test"""
        super().__init__()

        oh_item_remote_sleeping = SwitchItem.get_item("FernbedienungSchlafzimmer_Main")
        oh_item_remote_sleeping.listen_event(
            self.sleeping_remote, ValueChangeEventFilter(value="ON")
        )

        oh_item_remote_sleeping_long = SwitchItem.get_item(
            "FernbedienungSchlafzimmer_Main_Long"
        )
        oh_item_remote_sleeping_long.listen_event(
            self.sleeping_remote, ValueChangeEventFilter(value="ON")
        )

        oh_group_remote_terrace = GroupItem.get_item("gFernbedienungTerrasse")
        for oh_item in oh_group_remote_terrace.members:
            oh_item.listen_event(
                self.terrasse_remote, ValueChangeEventFilter(value="OFF")
            )

        logger.info("Mqtt rule initialized")

    def sleeping_remote(self, event):
        """key of remote control"""
        logger.info(
            "rule fired because of %s %s --> %s",
            event.name,
            event.old_value,
            event.value,
        )

        if "_Long" in event.name:
            longItem = "gLichterKeller_State"
            longItem2 = "gLichterHaus_State"
            if SwitchItem.get_item("longItem").get_value() == "ON":
                logger.info("turn %s OFF", longItem)
                self.openhab.send_command(longItem, "OFF")
            elif SwitchItem.get_item("longItem2").get_value() == "ON":
                logger.info("turn %s OFF", longItem2)
                self.openhab.send_command(longItem2, "OFF")
            else:
                alternativeItem = "LichtFlurKeller_State"
                logger.info("toggle %s", alternativeItem)
                self.openhab.post_update(
                    alternativeItem,
                    TOGGLE_MAP[str(SwitchItem.get_item(alternativeItem).get_value())],
                )

        else:
            shortItem = "LichtGaestezimmer_State"
            logger.info("toggle %s", shortItem)
            self.openhab.post_update(
                shortItem, TOGGLE_MAP[str(SwitchItem.get_item(shortItem).get_value())]
            )

    def terrasse_remote(self, event):
        """
        key of remote control

        Args:
            event (_type_): triggering event
        """
        logger.info(
            "rule fired because of %s %s --> %s",
            event.name,
            event.old_value,
            event.value,
        )

        if "_Long" in event.name:
            if "_MainButton_" in event.name:
                self.openhab.post_update(
                    "LichtTerrasse_Pergola_Alle_State",
                    TOGGLE_MAP[
                        str(
                            SwitchItem.get_item(
                                "LichtTerrasse_Pergola_Alle_State"
                            ).get_value()
                        )
                    ],
                )
            if "_Up_" in event.name:
                self.openhab.post_update("LichtTerrasse_Pergola_Alle_Dimmer", "100")
            if "_Left_" in event.name:
                self.openhab.post_update("LichtTerrasse_Pergola_Alle_ColorTemp", "0")
            if "_Right_" in event.name:
                self.openhab.post_update("LichtTerrasse_Pergola_Alle_ColorTemp", "100")
            if "_Down_" in event.name:
                self.openhab.post_update("LichtTerrasse_Pergola_Alle_Dimmer", "1")
        else:
            if "_MainButton" in event.name:
                self.openhab.post_update(
                    "LichtTerrasse_Pergola_Alle_State",
                    TOGGLE_MAP[
                        str(
                            SwitchItem.get_item(
                                "LichtTerrasse_Pergola_Alle_State"
                            ).get_value()
                        )
                    ],
                )
            if "_Up" in event.name:
                self.openhab.post_update("LichtTerrasse_Pergola_Alle_Dimmer_Step", "20")
            if "_Left" in event.name:
                self.openhab.post_update(
                    "LichtTerrasse_Pergola_Alle_ColorTemp_Step", "-20"
                )
            if "_Right" in event.name:
                self.openhab.post_update(
                    "LichtTerrasse_Pergola_Alle_ColorTemp_Step", "20"
                )
            if "_Down" in event.name:
                self.openhab.post_update(
                    "LichtTerrasse_Pergola_Alle_Dimmer_Step", "-20"
                )


Mqtt()
