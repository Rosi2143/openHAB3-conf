# https://habapp.readthedocs.io/en/latest/getting_started.html
import logging  # required for extended logging
from datetime import timedelta, datetime

import HABApp
from HABApp.openhab.items import SwitchItem, NumberItem
from HABApp.core.events import EventFilter, ValueChangeEventFilter, ValueChangeEvent

logger = logging.getLogger("Gardena")


class GardenaValveControl(HABApp.Rule):
    """activate and deactivate the valves"""

    def __init__(self):
        """initialize class"""
        super().__init__()

        # get the states
        self.valve1_state = SwitchItem.get_item("eGardenaVentilKontrolle_1_STATE")
        self.valve2_state = SwitchItem.get_item("eGardenaVentilKontrolle_2_STATE")
        self.valve3_state = SwitchItem.get_item("eGardenaVentilKontrolle_3_STATE")
        self.valve4_state = SwitchItem.get_item("eGardenaVentilKontrolle_4_STATE")
        self.valve5_state = SwitchItem.get_item("eGardenaVentilKontrolle_5_STATE")
        self.valve6_state = SwitchItem.get_item("eGardenaVentilKontrolle_6_STATE")

        self.valve1_3_state = SwitchItem.get_item("eGardenaVentilKontrolle_1_3_STATE")
        self.valve4_6_state = SwitchItem.get_item("eGardenaVentilKontrolle_4_6_STATE")

        # set the states
        self.valve1_state_set = SwitchItem.get_item("GardenaVentilKontrolle_1_STATE")
        self.valve2_state_set = SwitchItem.get_item("GardenaVentilKontrolle_2_STATE")
        self.valve3_state_set = SwitchItem.get_item("GardenaVentilKontrolle_3_STATE")
        self.valve4_state_set = SwitchItem.get_item("GardenaVentilKontrolle_4_STATE")
        self.valve5_state_set = SwitchItem.get_item("GardenaVentilKontrolle_5_STATE")
        self.valve6_state_set = SwitchItem.get_item("GardenaVentilKontrolle_6_STATE")

        self.valve1_3_state_set = SwitchItem.get_item(
            "GardenaVentilKontrolle_1_3_STATE"
        )
        self.valve4_6_state_set = SwitchItem.get_item(
            "GardenaVentilKontrolle_4_6_STATE"
        )

        self.valve1_state.listen_event(self.set_1_3_LED, ValueChangeEventFilter())
        self.valve2_state.listen_event(self.set_1_3_LED, ValueChangeEventFilter())
        self.valve3_state.listen_event(self.set_1_3_LED, ValueChangeEventFilter())
        self.valve4_state.listen_event(self.set_4_6_LED, ValueChangeEventFilter())
        self.valve5_state.listen_event(self.set_4_6_LED, ValueChangeEventFilter())
        self.valve6_state.listen_event(self.set_4_6_LED, ValueChangeEventFilter())

        logger.info("initialize gardena")

    def set_1_3_LED(self, event: ValueChangeEvent):
        """set the LED for valve 1-3

        Args:
            event: change event
        """

        logger.info(
            "set_1_3_LED: rule fired because of %s %s --> %s",
            event.name,
            event.old_value,
            event.value,
        )

        if (
            self.valve1_state.get_value() == "ON"
            or self.valve2_state.get_value() == "ON"
            or self.valve3_state.get_value() == "ON"
        ):
            logger.info("set LED 1-3: ON")
            self.valve1_3_state_set.on()
        else:
            logger.info("set LED 1-3: OFF")
            self.valve1_3_state_set.off()

    def set_4_6_LED(self, event: ValueChangeEvent):
        """set the LED for valve 4-6

        Args:
            event: change event
        """

        logger.info(
            "set_4_6_LED: rule fired because of %s %s --> %s",
            event.name,
            event.old_value,
            event.value,
        )
        if (
            self.valve4_state.get_value() == "ON"
            or self.valve5_state.get_value() == "ON"
            or self.valve6_state.get_value() == "ON"
        ):
            logger.info("set LED 4-6: ON")
            self.valve4_6_state_set.on()
        else:
            logger.info("set LED 4-6: OFF")
            self.valve4_6_state_set.off()


# Rules
GardenaValveControl()
