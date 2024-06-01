import logging  # required for extended logging
from datetime import datetime, timedelta
import os
import sys

import HABApp
from HABApp.openhab import transformations
from HABApp.openhab.items import DimmerItem, NumberItem, StringItem
from HABApp.core.events import (
    ValueChangeEvent,
    ValueChangeEventFilter,
)

logger = logging.getLogger("Indego")

param_file = "openhab"
OH_CONF = HABApp.DictParameter(param_file, "OH_Directories", default_value="")[
    "OPENHAB_CONF"
]
HABAPP_RULES = HABApp.DictParameter(param_file, "HABAPP_Directories", default_value="")[
    "HABAPP_RULES"
]

OH_ITEM_INDEGO_STATUS_TEXT = "Bosch_Indego_StatusText"
OH_ITEM_INDEGO_MOW_TIME = "Bosch_Indego_Last_MowTime"
OH_ITEM_INDEGO_PAUSE_TIME = "Bosch_Indego_Last_PauseTime"
OH_ITEM_INDEGO_COMMAND = "Bosch_Indego_Zustand_numerisch"
OH_ITEM_INDEGO_PROGRESS = "Bosch_Indego_Gras_schneiden"
INDEGO_MAP = transformations.map[
    "indego.map"
]  # load the transformation, can be used anywhere

OH_ITEM_RAIN_PRECIPATION_CURRENT = "openWeatherVorhersage_Current_PrecipitationAmount"
OH_ITEM_WEATHER_STATE_CURRENT = "openWeatherVorhersage_Wetterlage"
OH_ITEM_RAIN_PRECIPATION_FORECAST_3h = (
    "openWeatherVorhersage_ForecastHours03_PrecipitationAmount"
)
OH_ITEM_WEATHER_STATE_FORECAST_3h = "openWeatherVorhersage_Vorhergesagte_Wetterlage"

UPDATE_DURATION_SEC = 30

sys.path.append(os.path.join(OH_CONF, HABAPP_RULES))
from statemachines.IndegoStatemachine import IndegoStatemachine

indego_state_machine = IndegoStatemachine(name="Indego_S+500", logger=logger)


class Indego(HABApp.Rule):
    """determine the time it took to mow the lawn"""

    def __init__(self):
        """initialize the logger test"""
        super().__init__()

        self.statusTextOhItem = StringItem.get_item(OH_ITEM_INDEGO_STATUS_TEXT)
        self.statusTextOhItem.listen_event(
            self.indego_status_changes, ValueChangeEventFilter()
        )

        self.progressOhItem = DimmerItem.get_item(OH_ITEM_INDEGO_PROGRESS)

        self.rainCurrentOhItem = NumberItem.get_item(OH_ITEM_RAIN_PRECIPATION_CURRENT)
        self.rainCurrentOhItem.listen_event(
            self.weather_changed, ValueChangeEventFilter()
        )

        self.rainForecastOhItem = NumberItem.get_item(
            OH_ITEM_RAIN_PRECIPATION_FORECAST_3h
        )
        self.rainForecastOhItem.listen_event(
            self.weather_changed, ValueChangeEventFilter()
        )

        self.weatherCurrentOhItem = StringItem.get_item(OH_ITEM_WEATHER_STATE_CURRENT)
        self.weatherCurrentOhItem.listen_event(
            self.weather_changed, ValueChangeEventFilter()
        )

        self.weatherForecastOhItem = StringItem.get_item(
            OH_ITEM_WEATHER_STATE_FORECAST_3h
        )
        self.weatherForecastOhItem.listen_event(
            self.weather_changed, ValueChangeEventFilter()
        )

        self.indegoCommandOhItem = NumberItem.get_item(OH_ITEM_INDEGO_COMMAND)

        logger.info("Indego started. Current state = %s", self.statusTextOhItem.value)

        self.startTimeMow = datetime.now()
        self.mowingTime = 0
        self.startTimePause = datetime.now()
        self.pauseTime = timedelta(0)
        self.status = indego_state_machine.STATUS_UNKNOWN
        self.last_mowing_time = self.mowingTime
        self.last_pause_time = self.pauseTime
        self.next_timer_job = self.run.soon(
            self.indego_status_changes,
            ValueChangeEvent(name="start-up", value="none", old_value="none"),
        )
        self.next_timer_job = self.run.soon(
            self.weather_changed,
            ValueChangeEvent(name="start-up", value="none", old_value="none"),
        )

    def weather_changed(self, event: ValueChangeEvent):
        """
        send event to indego if rain starts
        Args:
            event (_type_): any weather change
        """
        logger.info(
            "rule fired because of %s %s --> %s",
            event.name,
            event.old_value,
            event.value,
        )

        self.rainCurrentOhItem = NumberItem.get_item(
            OH_ITEM_RAIN_PRECIPATION_CURRENT
        ).get_value()
        self.raintForecast = NumberItem.get_item(
            OH_ITEM_RAIN_PRECIPATION_FORECAST_3h
        ).get_value()
        self.weatherCurrentOhItem = StringItem.get_item(
            OH_ITEM_WEATHER_STATE_CURRENT
        ).get_value()
        self.weatherForecastOhItem = StringItem.get_item(
            OH_ITEM_WEATHER_STATE_FORECAST_3h
        ).get_value()

        if (
            self.rainCurrentOhItem > 0
            or self.raintForecast > 0
            or "rain" in str(self.weatherCurrentOhItem).lower()
            or "rain" in str(self.weatherForecastOhItem).lower()
        ):
            if self.statusTextOhItem != indego_state_machine.STATUS_DOCK:
                self.indegoCommandOhItem.oh_send_command(INDEGO_MAP["return_to_dock"])
                logger.info("Rain detected - Indego is returning to dock")
        else:
            if (
                indego_state_machine.current_state.name.lower()
                == indego_state_machine.STATUS_DOCK
            ):
                if self.progressOhItem.get_value() <= 80:
                    self.indegoCommandOhItem.oh_send_command(INDEGO_MAP["mow"])
                    logger.info("Indego is docked and rain stopped - starting mowing")

    def indego_status_changes(self, event: ValueChangeEvent):
        """
        send event to DoorLock statemachine if ReportedLock changes
        Args:
            event (_type_): any ReportedLock item
        """
        logger.info(
            "rule fired because of %s %s --> %s",
            event.name,
            event.old_value,
            event.value,
        )

        self.statusTextOhItem = str(
            StringItem.get_item(OH_ITEM_INDEGO_STATUS_TEXT).get_value()
        )

        indego_state_machine.set_reported_state(self.statusTextOhItem)

        if (
            indego_state_machine.current_state.name.lower()
            != indego_state_machine.STATUS_DOCK
        ):
            if self.next_timer_job != None:
                if self.next_timer_job.remaining() is not None:
                    self.next_timer_job.cancel()
                self.next_timer_job = None
            self.next_timer_job = self.run.every(
                timedelta(seconds=1),
                timedelta(seconds=UPDATE_DURATION_SEC),
                self.item_updater,
            )
        else:
            logger.info("Indego is docked - timer not started")

    def get_valid_time_format(self, time_in) -> str:
        return "{:02}:{:02}:{:02}".format(
            int(time_in / 3600),
            int((time_in / 60) % 60),
            int(time_in % 60),
        )

    def item_updater(self):
        """run a timer if required and update the indego action times"""
        logger.info("Update times")
        if (
            indego_state_machine.current_state.name.lower()
            != indego_state_machine.STATUS_DOCK
        ):
            logger.info("Restart timer")
        else:
            logger.info("Indego is docked - timer stopped")
            if self.next_timer_job.remaining() is not None:
                self.next_timer_job.cancel()
            self.next_timer_job = None
            return

        mowing_time, pause_time = indego_state_machine.get_action_timer()

        logger.info("MowTime  : %s", self.get_valid_time_format(mowing_time))
        if self.last_mowing_time != mowing_time:
            self.openhab.send_command(
                OH_ITEM_INDEGO_MOW_TIME, self.get_valid_time_format(mowing_time)
            )
            self.last_mowing_time = mowing_time

        logger.info("PauseTime: %s", self.get_valid_time_format(pause_time))
        if self.last_pause_time != pause_time:
            self.openhab.send_command(
                OH_ITEM_INDEGO_PAUSE_TIME, self.get_valid_time_format(pause_time)
            )
            self.last_pause_time = pause_time


Indego()
