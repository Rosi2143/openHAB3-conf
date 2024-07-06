# https://habapp.readthedocs.io/en/latest/getting_started.html
import logging  # required for extended logging
from datetime import timedelta, datetime

import HABApp
from HABApp.openhab.items import SwitchItem, NumberItem
from HABApp.core.events import EventFilter, ValueChangeEventFilter, ValueChangeEvent

logger = logging.getLogger("Pool")
POOLPUMP_ITEM_NAME = "SteckdosePool_State"
POOLPUMP_USAGE_ITEM_NAME = "SteckdosePool_PumpInUse"
POOLPUMP_DURATION_ITEM_NAME = "SteckdosePool_OnTime"
POOLPUMP_ACTIVATION_ITEM_NAME = "IstTag"


class MyPoolPumpTimer(HABApp.Rule):
    """activate and deactivate the poolpump"""

    def __init__(self, place: str):
        """initialize class and calculate the first time"""
        super().__init__()

        self.poolpump_state_item = SwitchItem.get_item(POOLPUMP_ITEM_NAME)
        self.poolpump_usage_item = SwitchItem.get_item(POOLPUMP_USAGE_ITEM_NAME)
        self.poolpump_duration_item = NumberItem.get_item(POOLPUMP_DURATION_ITEM_NAME)
        self.poolpump_activation_item = SwitchItem.get_item(
            POOLPUMP_ACTIVATION_ITEM_NAME
        )

        self.poolpump_activation_item.listen_event(
            self.activate_pump, ValueChangeEventFilter(value="OFF")
        )

        logger.info("initialize poolpump")
        logger.info("poolpump item: %s", self.poolpump_state_item.get_value())
        logger.info("poolpump usage item: %s", self.poolpump_usage_item.get_value())
        logger.info(
            "poolpump duration item: %s h", self.poolpump_duration_item.get_value()
        )
        logger.info(
            "poolpump activation item: ist Tag %s",
            self.poolpump_activation_item.get_value(),
        )

    def activate_pump(self, event: ValueChangeEvent):
        """activate the pump for a given time if the activation item is set to ON

        Args:
            state (datetime): duration for which the pump shall be ON
        """

        if self.poolpump_activation_item.get_value() == "ON":
            duration = int(self.poolpump_duration_item.get_value())
            logger.info("set pump: ON for %s h", self.place, duration)
            self.poolpump_state_item.on()
            self.run.at(
                time=timedelta(hours=duration),
                callback=self.deactivate_pump,
            )
        else:
            logger.info(
                "poolpump handling is deactivated by item %s",
                POOLPUMP_ACTIVATION_ITEM_NAME,
            )

    def deactivate_pump(self):
        """deactivate the watering"""
        logger.info("set poolpump: OFF")
        self.poolpump_state_item.off()


# Rules
MyPoolPumpTimer("oben")
