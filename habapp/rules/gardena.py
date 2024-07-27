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
        self.valve4_state = SwitchItem.get_item("eGardenaVentilKontrolle_1_3_STATE")
        self.valve5_state = SwitchItem.get_item("eGardenaVentilKontrolle_4_STATE")
        self.valve6_state = SwitchItem.get_item("eGardenaVentilKontrolle_5_STATE")
        self.valve7_state = SwitchItem.get_item("eGardenaVentilKontrolle_6_STATE")

        self.valve_all_state = SwitchItem.get_item("eGardenaVentilKontrolle_4_6_STATE")

        self.pump_state = SwitchItem.get_item("ePumpe_3_STATE")

        # set the states
        self.valve1_state_set = SwitchItem.get_item("GardenaVentilKontrolle_1_STATE")
        self.valve2_state_set = SwitchItem.get_item("GardenaVentilKontrolle_2_STATE")
        self.valve3_state_set = SwitchItem.get_item("GardenaVentilKontrolle_3_STATE")
        self.valve4_state_set = SwitchItem.get_item("GardenaVentilKontrolle_1_3_STATE")
        self.valve5_state_set = SwitchItem.get_item("GardenaVentilKontrolle_4_STATE")
        self.valve6_state_set = SwitchItem.get_item("GardenaVentilKontrolle_5_STATE")
        self.valve7_state_set = SwitchItem.get_item("GardenaVentilKontrolle_6_STATE")

        self.valve_all_state_set = SwitchItem.get_item(
            "GardenaVentilKontrolle_4_6_STATE"
        )

        self.pump_state_set = SwitchItem.get_item("ePumpe_4_STATE")

        # automatic program
        self.automatic = SwitchItem.get_item("GardenaAutomaticWatering")
        self.automatic_step = 0
        self.automatic_job = None
        self.automatic_times_sec = [10, 10, 10, 10, 10, 10, 10]

        self.valve1_state.listen_event(self.set_ON_LED, ValueChangeEventFilter())
        self.valve2_state.listen_event(self.set_ON_LED, ValueChangeEventFilter())
        self.valve3_state.listen_event(self.set_ON_LED, ValueChangeEventFilter())
        self.valve4_state.listen_event(self.set_ON_LED, ValueChangeEventFilter())
        self.valve5_state.listen_event(self.set_ON_LED, ValueChangeEventFilter())
        self.valve6_state.listen_event(self.set_ON_LED, ValueChangeEventFilter())
        self.valve7_state.listen_event(self.set_ON_LED, ValueChangeEventFilter())

        self.pump_state.listen_event(self.check_pump_state, ValueChangeEventFilter())

        self.automatic.listen_event(self.automatic_watering, ValueChangeEventFilter())

        logger.info("initialized gardena")
        logger.info("valve1_state: %s", self.valve1_state.get_value())
        logger.info("valve2_state: %s", self.valve2_state.get_value())
        logger.info("valve3_state: %s", self.valve3_state.get_value())
        logger.info("valve4_state: %s", self.valve4_state.get_value())
        logger.info("valve5_state: %s", self.valve5_state.get_value())
        logger.info("valve6_state: %s", self.valve6_state.get_value())
        logger.info("valve7_state: %s", self.valve7_state.get_value())
        logger.info("valve_all_state: %s", self.valve_all_state.get_value())

        logger.info("pump_state: %s", self.pump_state.get_value())

        logger.info("automatic: %s", self.automatic.get_value())

    def set_ON_LED(self, event: ValueChangeEvent):
        """set the LED if any valve is ON

        Args:
            event: change event
        """

        logger.info(
            "set_LED: rule fired because of %s %s --> %s",
            event.name,
            event.old_value,
            event.value,
        )

        if (
            self.valve1_state.get_value() == "ON"
            or self.valve2_state.get_value() == "ON"
            or self.valve3_state.get_value() == "ON"
            or self.valve4_state.get_value() == "ON"
            or self.valve5_state.get_value() == "ON"
            or self.valve6_state.get_value() == "ON"
            or self.valve7_state.get_value() == "ON"
        ):
            logger.info("set LED: ON")
            self.valve_all_state_set.on()
            if self.pump_state.get_value() == "OFF":
                logger.info("switch pump ON")
                self.pump_state_set.on()
            else:
                logger.info("pump already ON")
        else:
            logger.info("set LED: OFF")
            self.valve_all_state_set.off()

    def check_pump_state(self, event: ValueChangeEvent):
        """track state of pump

        Args:
            event: change event
        """

        logger.info(
            "check_pump_state: rule fired because of %s %s --> %s",
            event.name,
            event.old_value,
            event.value,
        )

        if event.value == "OFF":
            logger.info("switch all valves OFF")
            self.set_all_valve_off()
            if self.automatic_job is not None:
                self.automatic_job.cancel()
            self.automatic.off()

    def set_all_valve_off(self):
        logger.info("set all valves OFF")
        if self.valve1_state.get_value() == "ON":
            self.valve1_state_set.off()
        if self.valve2_state.get_value() == "ON":
            self.valve2_state_set.off()
        if self.valve3_state.get_value() == "ON":
            self.valve3_state_set.off()
        if self.valve4_state.get_value() == "ON":
            self.valve4_state_set.off()
        if self.valve5_state.get_value() == "ON":
            self.valve5_state_set.off()
        if self.valve6_state.get_value() == "ON":
            self.valve6_state_set.off()
        if self.valve7_state.get_value() == "ON":
            self.valve7_state_set.off()

    def change_automatic_state(self):
        logger.info("change automatic step old: %d", self.automatic_step)
        self.set_all_valve_off()
        start_timer = True
        if self.automatic_step == 1:
            self.valve1_state_set.on()
        if self.automatic_step == 2:
            self.valve2_state_set.on()
        if self.automatic_step == 3:
            self.valve3_state_set.on()
        if self.automatic_step == 4:
            self.valve4_state_set.on()
        if self.automatic_step == 5:
            self.valve5_state_set.on()
        if self.automatic_step == 6:
            self.valve6_state_set.on()
        if self.automatic_step == 7:
            self.valve7_state_set.on()
        if self.automatic_step == 8:
            logger.info("switch pump OFF - automatic done")
            self.pump_state_set.off()
            self.automatic.off()
            start_timer = False

        if start_timer:
            if self.automatic_job is not None:
                if self.automatic_job.remaining() is not None:
                    self.automatic_job.cancel()
            watering_time_sec = self.automatic_times_sec[self.automatic_step - 1]
            logger.info("start timer for %d sec", watering_time_sec)
            self.automatic_job = self.run.at(
                time=timedelta(seconds=watering_time_sec),
                callback=self.change_automatic_state,
            )
            self.automatic_step += 1
        else:
            self.automatic_job = None
            self.automatic_step = 0
        logger.info("change automatic step new: %d", self.automatic_step)

    def automatic_watering(self, event: ValueChangeEvent):
        """automatic watering

        Args:
            event: change event
        """

        logger.info(
            "automatic_watering: rule fired because of %s %s --> %s",
            event.name,
            event.old_value,
            event.value,
        )

        if event.value == "ON":
            logger.info("automatic watering ON")

            if self.valve_all_state.get_value() == "OFF":
                logger.info("Start programm")
                self.automatic_step = 1
            else:
                if self.valve1_state.get_value() == "ON":
                    self.automatic_step = 1
                if self.valve2_state.get_value() == "ON":
                    self.automatic_step = 2
                if self.valve3_state.get_value() == "ON":
                    self.automatic_step = 3
                if self.valve4_state.get_value() == "ON":
                    self.automatic_step = 4
                if self.valve5_state.get_value() == "ON":
                    self.automatic_step = 5
                if self.valve6_state.get_value() == "ON":
                    self.automatic_step = 6
                if self.valve7_state.get_value() == "ON":
                    self.automatic_step = 7
                logger.info("Continue programm with step %s", self.automatic_step)

            self.change_automatic_state()

        else:
            logger.info("automatic watering OFF at step %s", self.automatic_step)
            self.pump_state_set.off()
            if self.automatic_job is not None:
                if self.automatic_job.remaining() is not None:
                    self.automatic_job.cancel()


# Rules
GardenaValveControl()
