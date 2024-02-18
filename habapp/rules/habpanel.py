"""
This script handles event triggers for HABPanel items.
"""

import logging  # required for extended logging
from datetime import timedelta

import HABApp
from HABApp.openhab.items import ContactItem, NumberItem
from HABApp.openhab.events import ItemStateUpdatedEventFilter

logger = logging.getLogger("Habpanel")

BATTERY_MAX_CHARGE = 80
BATTERY_MIN_CHARGE = 40
OH_ITEM_NAME_BATTERY_LEVEL = "HABPanel_Battery_Level"
OH_ITEM_NAME_BATTERY_CHARGING = "HABPanel_Battery_Charging"
OH_ITEM_NAME_BATTERY_CHARGING_STATE = "HABPanelLadung_Betrieb"
OH_ITEM_NAME_MOTION = "HABPanel_Motion"
OH_ITEM_NAME_COMMAND = "HABPanel_Command"


class Habpanel(HABApp.Rule):
    """handle any zigbee device of IKEA"""

    def __init__(self):
        """initialize and create all elements for items defined in parameter file"""

        super().__init__()

        logger.info("Start")

        OH_ItemChargingState = NumberItem.get_item(OH_ITEM_NAME_BATTERY_LEVEL)
        OH_ItemChargingState.listen_event(
            self.check_charging_state, ItemStateUpdatedEventFilter()
        )
        self.run.every(
            timedelta(seconds=6),
            timedelta(minutes=5),
            self.check_charging_state,
            event=None,
        )

        OH_ItemMotionState = ContactItem.get_item(OH_ITEM_NAME_MOTION)
        OH_ItemMotionState.listen_event(
            self.proximity_alert, ItemStateUpdatedEventFilter()
        )
        logger.info("Started")

    def check_charging_state(self, event):
        """check if HABPanel needs charging"""

        if event:
            if event.getType() == "ItemStateUpdatedEvent":
                logger.info("rule fired because of %s", event.name)
            else:
                logger.info("rule fired because of cron-timer")

        battery_level = 0
        charging_state = False

        if self.openhab.item_exists(OH_ITEM_NAME_BATTERY_LEVEL):
            battery_level = NumberItem.get_item(OH_ITEM_NAME_BATTERY_LEVEL).get_value()
        else:
            logger.warning("Item %s not found", OH_ITEM_NAME_BATTERY_LEVEL)
        if self.openhab.item_exists(OH_ITEM_NAME_BATTERY_CHARGING):
            charging_state = (
                ContactItem.get_item(OH_ITEM_NAME_BATTERY_CHARGING).get_value()
                == "OPEN"
            )
        else:
            logger.warning("Item %s not found", OH_ITEM_NAME_BATTERY_LEVEL)

        logger.debug(
            "%s = %s --> LowBat = %s",
            OH_ITEM_NAME_BATTERY_LEVEL,
            battery_level,
            (battery_level < BATTERY_MIN_CHARGE),
        )

        logger.debug("%s = %s", OH_ITEM_NAME_BATTERY_CHARGING, charging_state)

        if (battery_level < BATTERY_MIN_CHARGE) and not charging_state:
            self.openhab.send_command(OH_ITEM_NAME_BATTERY_CHARGING_STATE, "ON")
            logger.info("start charging")
        elif (battery_level > BATTERY_MAX_CHARGE) and charging_state:
            self.openhab.send_command(OH_ITEM_NAME_BATTERY_CHARGING_STATE, "OFF")
            logger.info("stop charging")
        else:
            logger.info(
                "No change: ChargeState="
                + str(charging_state)
                + " ChargeLevel="
                + str(battery_level)
            )

    def proximity_alert(self, event):
        """turn HABPanel on if someone gets close"""

        if event:
            logger.info("rule fired because of %s --> %s", event.name, event.value)

        if str(str(event.value)) == "OPEN":
            self.openhab.send_command(OH_ITEM_NAME_COMMAND, "SCREEN_OFF")
        else:
            self.openhab.send_command(OH_ITEM_NAME_COMMAND, "SCREEN_ON")


Habpanel()
