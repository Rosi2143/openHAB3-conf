"""
This script handles event triggers for HABPanel items.
"""

import logging  # required for extended logging
from datetime import timedelta

import HABApp
from HABApp.openhab.items import ContactItem, NumberItem
from HABApp.openhab.events import ItemStateUpdatedEventFilter, ItemStateUpdatedEvent

logger = logging.getLogger("Habpanel")

BATTERY_MAX_CHARGE = 80
BATTERY_MIN_CHARGE = 0  # battery is broken 40
OH_ITEM_NAME_BATTERY_LEVEL = "HABPanel_Battery_Level"
OH_ITEM_NAME_BATTERY_CHARGING = "HABPanel_Battery_Charging"
OH_ITEM_NAME_BATTERY_CHARGING_STATE = "HABPanelLadung_Betrieb"
OH_ITEM_NAME_BATTERY_LOW_STATE = "HABPanel_Battery_Low"
OH_ITEM_NAME_MOTION = "HABPanel_Motion"
OH_ITEM_NAME_COMMAND = "HABPanel_Command"


class Habpanel(HABApp.Rule):
    """handle any zigbee device of IKEA"""

    def __init__(self):
        """initialize and create all elements for items defined in parameter file"""

        super().__init__()

        logger.info("Start")

        OH_ItemBatLowState = ContactItem.get_item(OH_ITEM_NAME_BATTERY_LOW_STATE)
        OH_ItemBatLowState.listen_event(
            self.check_charging_state, ItemStateUpdatedEventFilter()
        )

        OH_ItemChargingState = NumberItem.get_item(OH_ITEM_NAME_BATTERY_LEVEL)
        OH_ItemChargingState.listen_event(
            self.check_charging_state, ItemStateUpdatedEventFilter()
        )
        self.run.every(
            start_time=timedelta(seconds=6),
            interval=timedelta(minutes=5),
            callback=self.check_charging_state,
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
            if isinstance(event, ItemStateUpdatedEvent):
                logger.info("rule fired because of %s --> ", event.name, event.value)
            else:
                logger.info("rule fired because of cron-timer")

        battery_level = 0
        charging_state = False
        low_battery_state = False

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
        if self.openhab.item_exists(OH_ITEM_NAME_BATTERY_LOW_STATE):
            low_battery_state = ContactItem.get_item(
                OH_ITEM_NAME_BATTERY_LOW_STATE
            ).get_value() == "CLOSED" or (battery_level < BATTERY_MIN_CHARGE)
        else:
            logger.warning("Item %s not found", OH_ITEM_NAME_BATTERY_LOW_STATE)

        logger.debug(
            "%s = %s --> LowBat = %s",
            OH_ITEM_NAME_BATTERY_LEVEL,
            battery_level,
            low_battery_state,
        )

        logger.debug("%s = %s", OH_ITEM_NAME_BATTERY_CHARGING, charging_state)

        if low_battery_state and not charging_state:
            self.openhab.send_command(OH_ITEM_NAME_BATTERY_CHARGING_STATE, "ON")
            logger.info("start charging")
        elif not low_battery_state and charging_state:
            self.openhab.send_command(OH_ITEM_NAME_BATTERY_CHARGING_STATE, "OFF")
            logger.info("stop charging")
        else:
            logger.info(
                "No change: ChargeState=%s ChargeLevel=%s",
                str(charging_state),
                str(battery_level),
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
