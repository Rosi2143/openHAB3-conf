# https://habapp.readthedocs.io/en/latest/getting_started.html
import logging  # required for extended logging
from datetime import timedelta, datetime
import re

import HABApp
from HABApp.openhab.items import SwitchItem, NumberItem
from HABApp.core.events import ValueChangeEventFilter, ValueChangeEvent
from HABApp.openhab import transformations

logger = logging.getLogger("Gardena")

GARDANA_MAP = transformations.map[
    "gardena.map"
]  # load the transformation, can be used anywhere

GARDENA_AUTOMATE_LIST = [
    {"valve_name": "BeetSteckdose", "time_min": 10},
    {"valve_name": "RasenBäume", "time_min": 10},
    {"valve_name": "PoolTerrasse", "time_min": 10},
    {"valve_name": "PoolStraße", "time_min": 10},
    {"valve_name": "Terrasse", "time_min": 10},
    {"valve_name": "Erkerweg", "time_min": 10},
]

NUM_OF_VALVES = 7
MAX_EXPECTED_RAIN_MM = 5  # mm
ONTIME_UPDATE_INTERVAL_SEC = 10  # s


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
        self.valve7_state = SwitchItem.get_item("eGardenaVentilKontrolle_7_STATE")

        self.valve_list = [
            self.valve1_state,
            self.valve2_state,
            self.valve3_state,
            self.valve4_state,
            self.valve5_state,
            self.valve6_state,
            self.valve7_state,
        ]
        self.valve_all_state = SwitchItem.get_item("eGardenaVentilKontrolle_4_6_STATE")

        self.pump_state = SwitchItem.get_item("ePumpe_3_STATE")
        self.pump_running_state = SwitchItem.get_item("PumpeRunning")

        self.IsDay = SwitchItem.get_item("IstTag")
        self.currentRain = NumberItem.get_item(
            "openWeatherVorhersage_Current_PrecipitationAmount"
        )
        self.h03Rain = NumberItem.get_item(
            "openWeatherVorhersage_ForecastHours03_PrecipitationAmount"
        )
        self.h06Rain = NumberItem.get_item(
            "openWeatherVorhersage_ForecastHours06_PrecipitationAmount"
        )
        self.h09Rain = NumberItem.get_item(
            "openWeatherVorhersage_ForecastHours09_PrecipitationAmount"
        )
        self.h12Rain = NumberItem.get_item(
            "openWeatherVorhersage_ForecastHours12_PrecipitationAmount"
        )
        self.h15Rain = NumberItem.get_item(
            "openWeatherVorhersage_ForecastHours15_PrecipitationAmount"
        )
        self.h18Rain = NumberItem.get_item(
            "openWeatherVorhersage_ForecastHours18_PrecipitationAmount"
        )
        self.rain_list = [
            self.currentRain,
            self.h03Rain,
            self.h06Rain,
            self.h09Rain,
            self.h12Rain,
            self.h15Rain,
            self.h18Rain,
        ]

        # set the states
        self.valve1_state_set = SwitchItem.get_item("GardenaVentilKontrolle_1_STATE")
        self.valve2_state_set = SwitchItem.get_item("GardenaVentilKontrolle_2_STATE")
        self.valve3_state_set = SwitchItem.get_item("GardenaVentilKontrolle_3_STATE")
        self.valve4_state_set = SwitchItem.get_item("GardenaVentilKontrolle_4_STATE")
        self.valve5_state_set = SwitchItem.get_item("GardenaVentilKontrolle_5_STATE")
        self.valve6_state_set = SwitchItem.get_item("GardenaVentilKontrolle_6_STATE")
        self.valve7_state_set = SwitchItem.get_item("GardenaVentilKontrolle_7_STATE")

        self.valve_ONTIME_list = [0] * NUM_OF_VALVES

        self.valve_set_list = [
            self.valve1_state_set,
            self.valve2_state_set,
            self.valve3_state_set,
            self.valve4_state_set,
            self.valve5_state_set,
            self.valve6_state_set,
            self.valve7_state_set,
        ]
        self.valve_all_state_set = SwitchItem.get_item(
            "GardenaVentilKontrolle_4_6_STATE"
        )

        self.pump_state_set = SwitchItem.get_item("ePumpe_4_STATE")

        # automatic program
        self.automatic_active = SwitchItem.get_item("GardenaAutomaticWatering_Active")
        self.automatic = SwitchItem.get_item("GardenaAutomaticWatering")
        self.automatic_step = 0
        self.automatic_job = None

        self.counter_update_job = None

        self.valve1_state.listen_event(
            self.handle_valve_state_change, ValueChangeEventFilter()
        )
        self.valve2_state.listen_event(
            self.handle_valve_state_change, ValueChangeEventFilter()
        )
        self.valve3_state.listen_event(
            self.handle_valve_state_change, ValueChangeEventFilter()
        )
        self.valve4_state.listen_event(
            self.handle_valve_state_change, ValueChangeEventFilter()
        )
        self.valve5_state.listen_event(
            self.handle_valve_state_change, ValueChangeEventFilter()
        )
        self.valve6_state.listen_event(
            self.handle_valve_state_change, ValueChangeEventFilter()
        )
        self.valve7_state.listen_event(
            self.handle_valve_state_change, ValueChangeEventFilter()
        )

        self.pump_state.listen_event(self.check_pump_state, ValueChangeEventFilter())
        self.pump_running_state.listen_event(
            self.check_pump_running_state, ValueChangeEventFilter()
        )

        self.automatic.listen_event(self.automatic_watering, ValueChangeEventFilter())

        # environment data
        self.IsDay.listen_event(self.check_start_automatic)

        logger.info("\n\ninitialized gardena")
        for val_number in range(NUM_OF_VALVES):
            logger.info(
                "%s: %s",
                GARDANA_MAP[str(val_number + 1)],
                self.valve_list[val_number].get_value(),
            )
        logger.info("valve_all_state: %s", self.valve_all_state.get_value())

        logger.info("pump_state: %s", self.pump_state.get_value())
        logger.info("pump_running_state: %s", self.pump_running_state.get_value())

        logger.info("IsDay: %s", self.IsDay.get_value())
        logger.info(
            "previousRain: %s mm",
            sum(
                self.currentRain.get_persistence_data(
                    start_time=datetime.now() - timedelta(hours=18),
                    end_time=datetime.now(),
                )
                .get_data()
                .values()
            ),
        )
        logger.info("currentRain: %s mm", self.currentRain.get_value())
        logger.info(
            "expected rain: %0.2f mm",
            sum(rain_element.get_value() for rain_element in self.rain_list),
        )

        self.check_start_automatic()
        logger.info("automatic_active: %s", self.automatic_active.get_value())
        logger.info("automatic: %s", self.automatic.get_value())

    def handle_valve_state_change(self, event: ValueChangeEvent):
        """handle valve state change

        Args:
            event: change event
        """

        logger.info(
            "handle_valve_state_change: rule fired because of %s %s --> %s",
            event.name,
            event.old_value,
            event.value,
        )

        counter_item_name = event.name.replace("STATE", "ONTIME")
        counter_item = NumberItem.get_item(counter_item_name)

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

            # turn on pump
            if self.pump_state.get_value() == "OFF":
                logger.info("switch pump ON")
                self.pump_state_set.on()
            else:
                logger.info("pump already ON")

        else:
            logger.info("set LED: OFF")
            # turn off pump
            self.valve_all_state_set.off()

        valve_number = int(re.search(r"\d+", event.name)[0])

        if event.value == "ON":
            # start counter values
            counter_item.oh_send_command(0)
            if self.counter_update_job is not None:
                if self.counter_update_job.remaining() is not None:
                    self.counter_update_job.cancel()
            self.counter_update_job = self.run.at(
                time=timedelta(seconds=ONTIME_UPDATE_INTERVAL_SEC),
                callback=self.update_counter_item,
            )
            self.valve_ONTIME_list[valve_number - 1] = datetime.now()
        else:
            now = datetime.now()
            last_change = self.valve_ONTIME_list[valve_number - 1]
            time_on = (now - last_change).total_seconds()
            logger.info("last change: %s", last_change)
            logger.info("now: %s", now)
            logger.info("time on: %d", time_on)
            counter_item.oh_send_command(int(time_on))

    def update_counter_item(self):
        """update counter value of all currently running valves"""
        found_running_valve = False
        logger.info("update counter values")
        for val_number in range(NUM_OF_VALVES):
            if self.valve_list[val_number].get_value() == "ON":
                counter_item_name = self.valve_list[val_number].name.replace(
                    "STATE", "ONTIME"
                )
                counter_item = NumberItem.get_item(counter_item_name)
                counter_item.oh_send_command(
                    counter_item.get_value() + ONTIME_UPDATE_INTERVAL_SEC
                )
                logger.info(
                    "update counter %s: %d", counter_item_name, counter_item.get_value()
                )
                found_running_valve = True
        if found_running_valve:
            if self.counter_update_job is not None:
                if self.counter_update_job.remaining() is not None:
                    self.counter_update_job.cancel()
            self.run.at(
                time=timedelta(seconds=ONTIME_UPDATE_INTERVAL_SEC),
                callback=self.update_counter_item,
            )

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

    def check_pump_running_state(self, event: ValueChangeEvent):
        """track state of pump running

        Args:
            event: change event
        """

        logger.info(
            "check_pump_running_state: rule fired because of %s %s --> %s",
            event.name,
            event.old_value,
            event.value,
        )

    def set_all_valve_off(self):
        logger.info("set all valves OFF")
        for val_number in range(NUM_OF_VALVES):
            if self.valve_list[val_number].get_value() == "ON":
                self.valve_set_list[val_number].off()

    def change_automatic_state(self):
        logger.info("change automatic step old: %d", self.automatic_step)
        self.set_all_valve_off()
        start_timer = True
        if self.automatic_step < len(GARDENA_AUTOMATE_LIST):
            valve_name = GARDENA_AUTOMATE_LIST[self.automatic_step - 1]["valve_name"]
            valve_id = int(GARDANA_MAP[valve_name])
            self.valve_set_list[valve_id - 1].on()
            logger.info("switch valve %s ON (id=%d)", valve_name, valve_id)
        else:
            logger.info("switch pump OFF - automatic done")
            self.pump_state_set.off()
            self.automatic.off()
            start_timer = False

        if start_timer:
            if self.automatic_job is not None:
                if self.automatic_job.remaining() is not None:
                    self.automatic_job.cancel()
            watering_time_min = GARDENA_AUTOMATE_LIST[self.automatic_step - 1][
                "time_min"
            ]
            logger.info("start timer for %d min", watering_time_min)
            self.automatic_job = self.run.at(
                time=timedelta(minutes=watering_time_min),
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
                if self.automatic_step < len(GARDENA_AUTOMATE_LIST):
                    logger.info("Continue programm with step %s", self.automatic_step)
                else:
                    logger.info("undefined value for step %s", self.automatic_step)
                    self.automatic.off()
                    return

            self.change_automatic_state()

        else:
            logger.info("automatic watering OFF at step %s", self.automatic_step)
            self.pump_state_set.off()
            if self.automatic_job is not None:
                if self.automatic_job.remaining() is not None:
                    self.automatic_job.cancel()

    def check_start_automatic(self):
        """check if automatic watering should be started

        Args:
            event: change event
        """

        logger.info(
            "check_start_automatic",
        )

        expected_rain = sum(rain_element.get_value() for rain_element in self.rain_list)
        previous_rain = sum(
            self.currentRain.get_persistence_data(
                start_time=datetime.now() - timedelta(hours=18),
                end_time=datetime.now(),
            )
            .get_data()
            .values()
        )
        logger.info("expected rain: %0.2f mm", expected_rain)
        logger.info("previous rain: %0.2f mm", previous_rain)
        logger.info("automatic_active: %s", self.automatic_active.get_value())

        if self.automatic_active.get_value() == "OFF":
            return

        if (expected_rain < MAX_EXPECTED_RAIN_MM) and (
            previous_rain < MAX_EXPECTED_RAIN_MM
        ):
            self.automatic_watering(
                ValueChangeEvent(name="check_start", value="ON", old_value="OFF")
            )


# Rules
GardenaValveControl()
