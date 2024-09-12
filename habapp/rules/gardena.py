# https://habapp.readthedocs.io/en/latest/getting_started.html
import logging  # required for extended logging
from datetime import timedelta, datetime
import re

import HABApp
from HABApp.openhab.items import NumberItem, StringItem, SwitchItem
from HABApp.core.events import ValueChangeEventFilter, ValueChangeEvent
from HABApp.openhab import transformations

logger = logging.getLogger("Gardena")

GARDANA_MAP = transformations.map[
    "gardena.map"
]  # load the transformation, can be used anywhere

GARDENA_AUTOMATE_LIST_MORNING = [
    {"valve_name": "RasenBäume", "onTime_min": 30, "pauseTime_min": 40},
    {"valve_name": "PoolTerrasse", "onTime_min": 20, "pauseTime_min": 15},
    {"valve_name": "PoolStraße", "onTime_min": 20, "pauseTime_min": 25},
    {"valve_name": "Terrasse", "onTime_min": 20, "pauseTime_min": 10},
    {"valve_name": "Erkerweg", "onTime_min": 20, "pauseTime_min": 10},
    {"valve_name": "BeetSteckdose", "onTime_min": 20, "pauseTime_min": 10},
]

GARDENA_AUTOMATE_LIST_EVENING = [
    {"valve_name": "RasenBäume", "onTime_min": 15, "pauseTime_min": 40},
    {"valve_name": "PoolTerrasse", "onTime_min": 10, "pauseTime_min": 15},
    {"valve_name": "PoolStraße", "onTime_min": 10, "pauseTime_min": 25},
    {"valve_name": "Terrasse", "onTime_min": 10, "pauseTime_min": 10},
    {"valve_name": "Erkerweg", "onTime_min": 10, "pauseTime_min": 10},
    {"valve_name": "BeetSteckdose", "onTime_min": 10, "pauseTime_min": 10},
]

GARDENA_AUTOMATE_LIST_LAWN_FAST = [
    {"valve_name": "PoolTerrasse", "onTime_min": 10, "pauseTime_min": 1},
    {"valve_name": "PoolStraße", "onTime_min": 10, "pauseTime_min": 1},
    {"valve_name": "RasenBäume", "onTime_min": 15, "pauseTime_min": 1},
]

GARDENA_AUTOMATE_LIST_BEDS = [
    {"valve_name": "Terrasse", "onTime_min": 10, "pauseTime_min": 1},
    {"valve_name": "Erkerweg", "onTime_min": 10, "pauseTime_min": 1},
    {"valve_name": "BeetSteckdose", "onTime_min": 10, "pauseTime_min": 1},
]

GARDENA_AUTOMATE_MAP = {
    "morning": GARDENA_AUTOMATE_LIST_MORNING,
    "evening": GARDENA_AUTOMATE_LIST_EVENING,
    "lawn_fast": GARDENA_AUTOMATE_LIST_LAWN_FAST,
    "beds": GARDENA_AUTOMATE_LIST_BEDS,
}

NUM_OF_VALVES = 7
MAX_EXPECTED_RAIN_MM = 3  # mm
ONTIME_UPDATE_INTERVAL_SEC = 10  # s


class GardenaValveControl(HABApp.Rule):
    """activate and deactivate the valves"""

    def __init__(self):
        """initialize class"""
        super().__init__()

        # get the states
        self.valve1_state_item = SwitchItem.get_item("eGardenaVentilKontrolle_1_STATE")
        self.valve2_state_item = SwitchItem.get_item("eGardenaVentilKontrolle_2_STATE")
        self.valve3_state_item = SwitchItem.get_item("eGardenaVentilKontrolle_3_STATE")
        self.valve4_state_item = SwitchItem.get_item("eGardenaVentilKontrolle_4_STATE")
        self.valve5_state_item = SwitchItem.get_item("eGardenaVentilKontrolle_5_STATE")
        self.valve6_state_item = SwitchItem.get_item("eGardenaVentilKontrolle_6_STATE")
        self.valve7_state_item = SwitchItem.get_item("eGardenaVentilKontrolle_7_STATE")

        self.valve_list = [
            self.valve1_state_item,
            self.valve2_state_item,
            self.valve3_state_item,
            self.valve4_state_item,
            self.valve5_state_item,
            self.valve6_state_item,
            self.valve7_state_item,
        ]
        self.valve_all_state_item = SwitchItem.get_item(
            "eGardenaVentilKontrolle_4_6_STATE"
        )

        self.pump_state_item = SwitchItem.get_item("ePumpe_3_STATE")
        self.pump_running_state_item = SwitchItem.get_item("PumpeRunning")

        self.IsDay_item = SwitchItem.get_item("IstTag")
        self.currentRain_item = NumberItem.get_item(
            "openWeatherVorhersage_Current_PrecipitationAmount"
        )
        self.h03Rain_item = NumberItem.get_item(
            "openWeatherVorhersage_ForecastHours03_PrecipitationAmount"
        )
        self.h06Rain_item = NumberItem.get_item(
            "openWeatherVorhersage_ForecastHours06_PrecipitationAmount"
        )
        self.h09Rain_item = NumberItem.get_item(
            "openWeatherVorhersage_ForecastHours09_PrecipitationAmount"
        )
        self.h12Rain_item = NumberItem.get_item(
            "openWeatherVorhersage_ForecastHours12_PrecipitationAmount"
        )
        self.h15Rain_item = NumberItem.get_item(
            "openWeatherVorhersage_ForecastHours15_PrecipitationAmount"
        )
        self.h18Rain_item = NumberItem.get_item(
            "openWeatherVorhersage_ForecastHours18_PrecipitationAmount"
        )
        self.rain_list = [
            self.currentRain_item,
            self.h03Rain_item,
            self.h06Rain_item,
            self.h09Rain_item,
            self.h12Rain_item,
            self.h15Rain_item,
            self.h18Rain_item,
        ]

        # set the states
        self.valve1_state_set_item = SwitchItem.get_item(
            "GardenaVentilKontrolle_1_STATE"
        )
        self.valve2_state_set_item = SwitchItem.get_item(
            "GardenaVentilKontrolle_2_STATE"
        )
        self.valve3_state_set_item = SwitchItem.get_item(
            "GardenaVentilKontrolle_3_STATE"
        )
        self.valve4_state_set_item = SwitchItem.get_item(
            "GardenaVentilKontrolle_4_STATE"
        )
        self.valve5_state_set_item = SwitchItem.get_item(
            "GardenaVentilKontrolle_5_STATE"
        )
        self.valve6_state_set_item = SwitchItem.get_item(
            "GardenaVentilKontrolle_6_STATE"
        )
        self.valve7_state_set_item = SwitchItem.get_item(
            "GardenaVentilKontrolle_7_STATE"
        )

        self.valve_ONTIME_list = [0] * NUM_OF_VALVES

        self.valve_set_list = [
            self.valve1_state_set_item,
            self.valve2_state_set_item,
            self.valve3_state_set_item,
            self.valve4_state_set_item,
            self.valve5_state_set_item,
            self.valve6_state_set_item,
            self.valve7_state_set_item,
        ]
        self.valve_all_state_set_item = SwitchItem.get_item(
            "GardenaVentilKontrolle_4_6_STATE"
        )

        self.pump_state_set_item = SwitchItem.get_item("ePumpe_4_STATE")

        # automatic program
        self.automatic_activated_item = SwitchItem.get_item(
            "GardenaAutomaticWatering_Active"
        )
        self.automatic_running_item = SwitchItem.get_item("GardenaAutomaticWatering")
        self.automatic_step_item = NumberItem.get_item("GardenaAutomaticStep")
        self.automatic_selection_item = StringItem.get_item("GardenaAutomaticSelect")
        self.automatic_job = None
        self.automatic_state = "OFF"
        self.gardena_automate_list = GARDENA_AUTOMATE_MAP[
            self.automatic_selection_item.get_value("morning")
        ]

        self.counter_update_job = None

        self.valve1_state_item.listen_event(
            self.handle_valve_state_change, ValueChangeEventFilter()
        )
        self.valve2_state_item.listen_event(
            self.handle_valve_state_change, ValueChangeEventFilter()
        )
        self.valve3_state_item.listen_event(
            self.handle_valve_state_change, ValueChangeEventFilter()
        )
        self.valve4_state_item.listen_event(
            self.handle_valve_state_change, ValueChangeEventFilter()
        )
        self.valve5_state_item.listen_event(
            self.handle_valve_state_change, ValueChangeEventFilter()
        )
        self.valve6_state_item.listen_event(
            self.handle_valve_state_change, ValueChangeEventFilter()
        )
        self.valve7_state_item.listen_event(
            self.handle_valve_state_change, ValueChangeEventFilter()
        )

        self.pump_state_item.listen_event(
            self.check_pump_state, ValueChangeEventFilter()
        )
        self.pump_running_state_item.listen_event(
            self.check_pump_running_state, ValueChangeEventFilter()
        )

        self.automatic_running_item.listen_event(
            self.automatic_watering, ValueChangeEventFilter()
        )
        self.automatic_selection_item.listen_event(
            self.automatic_select, ValueChangeEventFilter()
        )

        # environment data
        self.IsDay_item.listen_event(
            self.check_start_automatic, ValueChangeEventFilter(value="ON")
        )

        logger.info("\n\ninitialized gardena")
        for val_number in range(NUM_OF_VALVES):
            logger.info(
                "%s: %s",
                GARDANA_MAP[str(val_number + 1)],
                self.valve_list[val_number].get_value(),
            )
        logger.info("valve_all_state: %s", self.valve_all_state_item.get_value())

        logger.info("pump_state: %s", self.pump_state_item.get_value())
        logger.info("pump_running_state: %s", self.pump_running_state_item.get_value())

        logger.info("IsDay: %s", self.IsDay_item.get_value())
        logger.info(
            "previousRain: %s mm",
            sum(
                self.currentRain_item.get_persistence_data(
                    start_time=datetime.now() - timedelta(hours=18),
                    end_time=datetime.now(),
                )
                .get_data()
                .values()
            ),
        )
        logger.info("currentRain: %s mm", self.currentRain_item.get_value())
        logger.info(
            "expected rain: %0.2f mm",
            sum(rain_element.get_value() for rain_element in self.rain_list),
        )

        #        self.check_start_automatic(ValueChangeEvent(name="check_start", value="ON", old_value="OFF"))
        logger.info(
            "automatic_activated: %s", self.automatic_activated_item.get_value()
        )
        logger.info("automatic_running: %s", self.automatic_running_item.get_value())
        logger.info("automatic_step: %s", self.automatic_step_item.get_value())
        logger.info(
            "automatic_selection: %s", self.automatic_selection_item.get_value()
        )
        logger.info("automatic list: %s", self.gardena_automate_list)

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
            self.valve1_state_item.get_value() == "ON"
            or self.valve2_state_item.get_value() == "ON"
            or self.valve3_state_item.get_value() == "ON"
            or self.valve4_state_item.get_value() == "ON"
            or self.valve5_state_item.get_value() == "ON"
            or self.valve6_state_item.get_value() == "ON"
            or self.valve7_state_item.get_value() == "ON"
        ):
            logger.info("set LED: ON")
            self.valve_all_state_set_item.oh_send_command("ON")

            # turn on pump
            if self.pump_state_item.get_value() == "OFF":
                logger.info("switch pump ON")
                self.pump_state_set_item.oh_send_command("ON")
            else:
                logger.info("pump already ON")

        else:
            logger.info("set LED: OFF")
            # turn off pump
            self.valve_all_state_set_item.oh_send_command("OFF")

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
            if last_change == 0:
                last_change = now
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
                if self.counter_update_job.remaining() is not None:
                    self.automatic_job.cancel()
            self.automatic_running_item.oh_send_command("OFF")

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
                self.valve_set_list[val_number].oh_send_command("OFF")

    def reset_on_time(self):
        logger.info("reset on time")
        for val_number in range(NUM_OF_VALVES):
            counter_item_name = self.valve_list[val_number].name.replace(
                "STATE", "ONTIME"
            )
            counter_item = NumberItem.get_item(counter_item_name)
            counter_item.oh_send_command(0)

    def change_automatic_state(self):
        automatic_step = max(1, self.automatic_step_item.get_value())
        logger.info("change automatic step old: %d", automatic_step)
        self.set_all_valve_off()
        start_timer = True
        if automatic_step <= len(self.gardena_automate_list):
            if self.automatic_state == "watering":
                valve_name = self.gardena_automate_list[automatic_step - 1][
                    "valve_name"
                ]
                valve_id = int(GARDANA_MAP[valve_name])
                self.valve_set_list[valve_id - 1].oh_send_command("ON")
                logger.info("switch valve %s ON (id=%d)", valve_name, valve_id)
            else:
                logger.info(
                    "not setting valve -- automatic state: %s", self.automatic_state
                )
        else:
            logger.info("switch pump OFF - automatic done")
            self.pump_state_set_item.oh_send_command("OFF")
            self.automatic_running_item.oh_send_command("OFF")
            start_timer = False

        if start_timer:
            if self.automatic_job is not None:
                if self.automatic_job.remaining() is not None:
                    self.automatic_job.cancel()
            if self.automatic_state == "watering":
                time_min = self.gardena_automate_list[automatic_step - 1]["onTime_min"]
                logger.info("start watering timer for %d min", time_min)
                self.automatic_state = "pausing"
            else:
                time_min = self.gardena_automate_list[automatic_step - 1][
                    "pauseTime_min"
                ]
                logger.info("start pause timer for %d min", time_min)
                self.automatic_state = "watering"
                self.automatic_step_item.oh_send_command(automatic_step + 1)

            self.automatic_job = self.run.at(
                time=timedelta(minutes=time_min),
                callback=self.change_automatic_state,
            )
        else:
            self.automatic_job = None
            self.automatic_step_item.oh_send_command(0)
            self.automatic_state = "OFF"
        logger.info(
            "change automatic step new: %d", self.automatic_step_item.get_value()
        )

    def automatic_select(self, event: ValueChangeEvent):
        """automatic selection

        Args:
            event: change event
        """

        logger.info(
            "automatic_selection: rule fired because of %s %s --> %s",
            event.name,
            event.old_value,
            event.value,
        )
        self.gardena_automate_list = GARDENA_AUTOMATE_MAP[event.value]
        logger.info("automatic selection: %s", event.value)
        logger.info("automatic selection: %s", self.gardena_automate_list)

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

        automatic_step = max(1, self.automatic_step_item.get_value())
        if event.value == "ON":
            logger.info("automatic watering ON")
            self.automatic_running_item.oh_send_command("ON")

            numOfSteps = len(self.gardena_automate_list)
            if self.valve_all_state_item.get_value() == "OFF":
                logger.info("Start programm at step %d/%d", automatic_step, numOfSteps)
                self.reset_on_time()
            else:
                if automatic_step < len(self.gardena_automate_list):
                    logger.info(
                        "Continue programm with step %d/%d", automatic_step, numOfSteps
                    )
                else:
                    logger.info(
                        "undefined value for step %d/%d", automatic_step, numOfSteps
                    )
                    self.automatic_running_item.oh_send_command("OFF")
                    return

            self.automatic_state = "watering"
            self.change_automatic_state()

        else:
            logger.info("automatic watering OFF at step %s", automatic_step)
            self.pump_state_set_item.oh_send_command("OFF")
            if self.automatic_job is not None:
                if self.automatic_job.remaining() is not None:
                    self.automatic_job.cancel()

    def check_start_automatic(self, event: ValueChangeEvent):
        """check if automatic watering should be started

        Args:
            event: change event
        """
        logger.info(
            "\n###############################################################\n"
        )

        logger.info(
            "check_start_automatic: rule fired because of %s %s --> %s",
            event.name,
            event.old_value,
            event.value,
        )

        expected_rain = sum(rain_element.get_value() for rain_element in self.rain_list)
        previous_rain = sum(
            self.currentRain_item.get_persistence_data(
                start_time=datetime.now() - timedelta(hours=18),
                end_time=datetime.now(),
            )
            .get_data()
            .values()
        )
        logger.info("expected rain: %0.2f mm", expected_rain)
        logger.info("previous rain: %0.2f mm", previous_rain)
        logger.info("automatic_active: %s", self.automatic_activated_item.get_value())

        if self.automatic_activated_item.get_value() == "OFF":
            logger.info("automatic watering is not active")
            return

        if (expected_rain + previous_rain) < MAX_EXPECTED_RAIN_MM:
            self.automatic_step_item.oh_send_command(1)
            self.automatic_selection_item.oh_send_command("morning")

            self.automatic_watering(
                ValueChangeEvent(name="check_start", value="ON", old_value="OFF"),
            )
        else:
            logger.info("no automatic watering because of rain")


# Rules
GardenaValveControl()
