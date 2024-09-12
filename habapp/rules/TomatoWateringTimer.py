# https://habapp.readthedocs.io/en/latest/getting_started.html
import logging  # required for extended logging
from datetime import timedelta, datetime
import math

import HABApp
from HABApp.core.errors import ItemNotFoundException
from HABApp.openhab.items import StringItem, SwitchItem, NumberItem, Thing
from HABApp.openhab.definitions import ThingStatusEnum
from HABApp.openhab.events import ThingStatusInfoChangedEvent
from HABApp.core.events import EventFilter, ValueChangeEventFilter, ValueChangeEvent

logger = logging.getLogger("TomatoTimer")

TIME_FOR_WATERING_MIN = 2
Tomato_Set = {
    "oben": {
        "THING_UID_PLUG": "hue:device:ecb5fafffe2c8738:25",
        "DEVICE_NAME_PLUG_STATE": "AussenSteckdose_Betrieb",
    },
    "unten": {
        "ITEM_UID_PLUG": "SteckdoseRosenbogen_Online",
        "DEVICE_NAME_PLUG_STATE": "SteckdoseRosenbogen_State",
    },
}
INITIAL_DELAY = 180
RAIN_EFFECT_FACTOR = 500

TEMPERATURE_EFFECT_BASE = 25
TEMPERATURE_EFFECT_FACTOR = 2
HUMIDITY_EFFECT_BASE = 100
HUMIDITY_EFFECT_FACTOR = 2
WIND_EFFECT_FACTOR = 5
LIGHT_EFFECT_FACTOR = 5

TOMATO_START_MONTH = 4
TOMATO_END_MOTNH = 10


class MyTomatoTimer(HABApp.Rule):
    """check when the tomatoes should get more water
    activate the pump at this time for a specified
    duration"""

    def __init__(self, place: str):
        """initialize class and calculate the first time"""
        super().__init__()

        self.device_name_plug_state = Tomato_Set[place]["DEVICE_NAME_PLUG_STATE"]
        self.place = place
        if "THING_UID_PLUG" in Tomato_Set[place]:
            self.thing_uid_plug = Tomato_Set[place]["THING_UID_PLUG"]
            self.item_uid_plug = None
        elif "ITEM_UID_PLUG" in Tomato_Set[place]:
            self.thing_uid_plug = None
            self.item_uid_plug = Tomato_Set[place]["ITEM_UID_PLUG"]
        else:
            logger.error("%s:No plug defined", place)
        self.thing_offline_on_request = False
        self.now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        logger.info("%s:Started TomatoTimer: %s", self.place, self.now)
        self.dark_outside_item = StringItem.get_item("Sonnendaten_Sonnenphase")
        dark_outside_state = self.is_dark_outside(
            self.dark_outside_item.get_value("OFF")
        )
        logger.info("%s:is it dark outside? --> %s", self.place, dark_outside_state)

        self.watering_active_item = SwitchItem.get_item(self.device_name_plug_state)
        watering_active_state = self.watering_active_item.get_value("OFF")
        logger.info("%s:watering active? --> %s", self.place, watering_active_state)

        self.watering_state = watering_active_state == "ON"

        self.get_plug_thing_or_item()
        self.now = ""  # reset now to disable timer_expired workaround

        # get config items from UI
        self.initial_delay_item = NumberItem.get_item("Tomato_Initial_Delay")
        self.initial_delay = self.initial_delay_item.get_value(INITIAL_DELAY)
        self.initial_delay_item.listen_event(
            self.initial_delay_changed, ValueChangeEventFilter()
        )

        self.rain_effect_item = NumberItem.get_item("Tomato_RainEffect_Factor")
        self.rain_effect = self.rain_effect_item.get_value(RAIN_EFFECT_FACTOR)
        self.rain_effect_item.listen_event(
            self.rain_effect_changed, ValueChangeEventFilter()
        )

        self.tomato_timer = self.run.soon(self.timer_expired)

    def initial_delay_changed(self, event: ValueChangeEvent):
        """handle changes in initial delay item

        Args:
            event (ValueChangeEvent): event that lead to this change
        """
        logger.info(
            "%s:rule fired because of %s %s --> %s",
            self.place,
            event.name,
            event.old_value,
            event.value,
        )
        self.initial_delay = event.value
        self.run.soon(self.timer_expired)

    def rain_effect_changed(self, event: ValueChangeEvent):
        """handle changes in initial delay item

        Args:
            event (ValueChangeEvent): event that lead to this change
        """
        logger.info(
            "%s:rule fired because of %s %s --> %s",
            self.place,
            event.name,
            event.old_value,
            event.value,
        )
        self.rain_effect = event.value
        self.run.soon(self.timer_expired)

    def thing_status_changed(self, event: ThingStatusInfoChangedEvent):
        """handle changes in plug thing status

        Args:
            event (ThingStatusInfoChangedEvent): event that lead to this change
        """
        logger.info(
            "%s:rule fired because of %s %s --> %s",
            self.place,
            event.name,
            event.old_status,
            event.status,
        )
        if event.status == ThingStatusEnum.ONLINE:
            if self.thing_offline_on_request:
                logger.info("%s:Activate plug now", self.place)
                self.thing_offline_on_request = False
                self.activate_watering()
        else:
            logger.info("%s:%s: Details = %s", self.place, event.name, event.detail)

    def item_status_changed(self, event: ValueChangeEvent):
        """handle changes in plug thing status

        Args:
            event (ValueChangeEvent): event that lead to this change
        """
        logger.info(
            "%s:rule fired because of %s %s --> %s",
            self.place,
            event.name,
            event.old_value,
            event.value,
        )
        if event.value == "ON":
            if self.thing_offline_on_request:
                logger.info("%s:Activate plug now", self.place)
                self.thing_offline_on_request = False
                self.activate_watering()
        else:
            logger.info("%s:%s: Details = %s", self.place, event.name, event.detail)

    def get_plug_thing_or_item(self):
        if self.thing_uid_plug is not None:
            try:
                self.plug_thing_or_item = Thing.get_item(self.thing_uid_plug)
                self.plug_thing_or_item.listen_event(
                    self.thing_status_changed,
                    EventFilter(ThingStatusInfoChangedEvent),
                )
                logger.info(
                    "%s:Thing   = %s", self.place, self.plug_thing_or_item.label
                )
                logger.info(
                    "%s:Status  = %s", self.place, self.plug_thing_or_item.status
                )
            except ItemNotFoundException:
                logger.warning(
                    "%s:Thing %s does not exist",
                    self.place,
                    self.device_name_plug_state,
                )
                self.plug_thing_or_item = None
        elif self.item_uid_plug is not None:
            try:
                self.plug_thing_or_item = SwitchItem.get_item(self.item_uid_plug)
                self.plug_thing_or_item.listen_event(
                    self.item_status_changed, ValueChangeEventFilter()
                )
                logger.info("%s:Item   = %s", self.place, self.plug_thing_or_item.label)
                logger.info(
                    "%s:Status = %s", self.place, self.plug_thing_or_item.get_value()
                )
            except ItemNotFoundException:
                logger.warning(
                    "%s:Item %s does not exist", self.place, self.device_name_plug_state
                )
                self.plug_thing_or_item = None

    def get_next_start(self):
        """determine when the pump shall be activated the next time
           This takes the following data into consideration

           - current/forcast weather
           - current/forcast rain
           - current/forcast temperature
           - current/forcast humidity
           - current/forcast wind

           - current sun exposure

        Returns:
            int: delay in minutes
        """
        logger.info("%s:calculate the next start time", self.place)
        current_weather_item = StringItem.get_item("openWeatherVorhersage_Wetterlage")
        current_weather_state = current_weather_item.get_value()
        logger.info(
            "%s:Wetter: Wetterlage               ---   %s",
            self.place,
            current_weather_state,
        )
        forecast_weather_item = StringItem.get_item(
            "openWeatherVorhersage_Vorhergesagte_Wetterlage"
        )
        forecast_weather_state = forecast_weather_item.get_value()
        logger.info(
            "%s:Wetter: Vorhergesagte_Wetterlage ---   %s",
            self.place,
            forecast_weather_state,
        )

        current_rain_item = NumberItem.get_item(
            "openWeatherVorhersage_Current_PrecipitationAmount"
        )
        current_rain_state = current_rain_item.get_value()
        logger.info(
            "%s:Wetter: Current_PrecipitationAmount         ---   %0.1fmm",
            self.place,
            current_rain_state,
        )
        forecast_rain_item = NumberItem.get_item(
            "openWeatherVorhersage_ForecastHours03_PrecipitationAmount"
        )
        forecast_rain_state = forecast_rain_item.get_value()
        logger.info(
            "%s:Wetter: ForecastHours03_PrecipitationAmount ---   %0.1fmm",
            self.place,
            forecast_rain_state,
        )

        current_temperature_item = NumberItem.get_item(
            "openWeatherVorhersage_Current_Temperature"
        )
        current_temperature_state = current_temperature_item.get_value()
        logger.info(
            "%s:Wetter: Current_Temperature         ---   %0.1f°C",
            self.place,
            current_temperature_state,
        )
        forecast_temperature_item = NumberItem.get_item(
            "openWeatherVorhersage_ForecastHours03_Temperature"
        )
        forecast_temperature_state = forecast_temperature_item.get_value()
        logger.info(
            "%s:Wetter: ForecastHours03_Temperature ---   %0.1f°C",
            self.place,
            forecast_temperature_state,
        )

        current_humidity_item = NumberItem.get_item(
            "openWeatherVorhersage_Luftfeuchtigkeit"
        )
        current_humidity_state = current_humidity_item.get_value()
        logger.info(
            "%s:Wetter: Luftfeuchtigkeit               ---   %0.1f%%",
            self.place,
            current_humidity_state,
        )
        forecast_humidity_item = NumberItem.get_item(
            "openWeatherVorhersage_Vorhergesagte_Luftfeuchtigkeit"
        )
        forecast_humidity_state = forecast_humidity_item.get_value()
        logger.info(
            "%s:Wetter: Vorhergesagte_Luftfeuchtigkeit ---   %0.1f%%",
            self.place,
            forecast_humidity_state,
        )

        current_wind_item = NumberItem.get_item(
            "openWeatherVorhersage_Windgeschwindigkeit"
        )
        current_wind_state = current_wind_item.get_value()
        logger.info(
            "%s:Wetter: Windgeschwindigkeit               ---   %skm/h",
            self.place,
            current_wind_state,
        )
        forecast_wind_item = NumberItem.get_item(
            "openWeatherVorhersage_Vorhergesagte_Windgeschwindigkeit"
        )
        forecast_wind_state = forecast_wind_item.get_value()
        logger.info(
            "%s:Wetter: Vorhergesagte_Windgeschwindigkeit ---   %skm/h",
            self.place,
            forecast_wind_state,
        )

        current_sun_exposure_item = NumberItem.get_item("Sonnendaten_DirekteStrahlung")
        current_sun_exposure_state = current_sun_exposure_item.get_value()
        logger.info(
            "%s:Sonnendaten_DirekteStrahlung ---   %dlx",
            self.place,
            current_sun_exposure_state,
        )
        current_sun_exposure_driveway_item = NumberItem.get_item(
            "LichtSensorEinfahrt_Beleuchtungsstaerke"
        )
        current_sun_exposure_driveway_state = (
            current_sun_exposure_driveway_item.get_value(0)
        )
        logger.info(
            "%s:Licht: SensorEinfahrt ---   %0.2flx",
            self.place,
            current_sun_exposure_driveway_state,
        )
        current_sun_exposure_orielway_item = NumberItem.get_item(
            "LichtSensorErkerWeg_Beleuchtungsstaerke"
        )
        current_sun_exposure_orielway_state = (
            current_sun_exposure_orielway_item.get_value(0)
        )
        logger.info(
            "%s:Licht: SensorErkerWeg ---   %0.2flx",
            self.place,
            current_sun_exposure_orielway_state,
        )
        current_sun_exposure_well_item = NumberItem.get_item(
            "LichtSensorBrunnen_Beleuchtungsstarke"
        )
        current_sun_exposure_well_state = current_sun_exposure_well_item.get_value(0)
        logger.info(
            "%s:Licht: SensorBrunnen   ---   %0.2flx",
            self.place,
            current_sun_exposure_well_state,
        )

        if self.plug_thing_or_item is None:
            self.get_plug_thing_or_item()

        calculated_delay = self.initial_delay
        if self.plug_thing_or_item is not None:
            offline = False
            if self.thing_uid_plug is not None:
                if self.plug_thing_or_item.status != ThingStatusEnum.ONLINE:
                    offline = True
            if self.item_uid_plug is not None:
                if self.plug_thing_or_item.get_value("OFF") != "ON":
                    offline = True
            if offline:
                logger.info(
                    "%s: Details = %s",
                    self.place,
                    self.plug_thing_or_item.label,
                    self.plug_thing_or_item.status_detail,
                )
                logger.info("%s:Saving ON-request", self.place)
                self.thing_offline_on_request = True
            else:
                rain_effect_min = (
                    (current_rain_state + forecast_rain_state) / 2
                ) * self.rain_effect
                logger.info(
                    "%s:rain_effect_min  ---   %0.1fmin", self.place, rain_effect_min
                )

                temperature_effect_min = (
                    math.log2(
                        max(
                            1.0000001,
                            (
                                (current_temperature_state + forecast_temperature_state)
                                / 2
                            )
                            - TEMPERATURE_EFFECT_BASE,
                        )
                    )
                    * TEMPERATURE_EFFECT_FACTOR
                )
                logger.info(
                    "%s:temperature_effect_min  ---   %0.1fmin",
                    self.place,
                    temperature_effect_min,
                )

                humidity_effect_min = (
                    math.log2(
                        HUMIDITY_EFFECT_BASE
                        - ((current_humidity_state + forecast_humidity_state) / 2)
                    )
                    * HUMIDITY_EFFECT_FACTOR
                )
                logger.info(
                    "%s:humidity_effect_min  ---   %0.1fmin",
                    self.place,
                    humidity_effect_min,
                )

                wind_effect_min = (
                    math.log10((current_wind_state + forecast_wind_state) / 2)
                    * WIND_EFFECT_FACTOR
                )
                logger.info(
                    "%s:wind_effect_min      ---   %0.1fmin",
                    self.place,
                    wind_effect_min,
                )

                light_effect_min = (
                    math.log10(
                        (
                            current_sun_exposure_driveway_state
                            + current_sun_exposure_orielway_state
                            + current_sun_exposure_well_state
                        )
                        / 3
                    )
                    * LIGHT_EFFECT_FACTOR
                )
                logger.info(
                    "%s:light_effect_min     ---   %0.1fmin",
                    self.place,
                    light_effect_min,
                )

                calculated_delay = (
                    self.initial_delay
                    + rain_effect_min
                    - humidity_effect_min
                    - wind_effect_min
                    - light_effect_min
                )

        logger.info("%s:calculated delay = %0.1fmin", self.place, calculated_delay)
        now = datetime.now()
        midnight = now.replace(hour=23, minute=59, second=59, microsecond=999999)
        time_till_midnight = (midnight - now).total_seconds() / 60

        if calculated_delay > time_till_midnight:
            calculated_delay = time_till_midnight
            logger.info(
                "%s:reduced delay to %0.1fmin (midnight today)",
                self.place,
                calculated_delay,
            )
        return calculated_delay

    def timer_expired(self):
        """TomatoTimer expired"""

        logger.info("%s:TomatoTimer expired", self.place)

        self.tomato_timer = None
        # workaround as timer_expired is executed twice for on_sunrise
        now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        if now == self.now:
            logger.info("%s:TomatoTimer expired now already", self.place)
            return
        else:
            self.now = now

        current_month = datetime.now().month
        if (current_month < TOMATO_START_MONTH) or (current_month > TOMATO_END_MOTNH):
            self.tomato_timer = self.run.on_sunrise(self.timer_expired).offset(
                timedelta(minutes=30)
            )
            logger.info(
                "%s:no tomato time - next trigger time: %s",
                self.place,
                self.tomato_timer.get_next_run().strftime("%d/%m/%Y %H:%M:%S"),
            )
        else:
            dark_outside_state = self.dark_outside_item.get_value("OFF")
            is_dark = self.is_dark_outside(dark_outside_state)
            if is_dark:
                logger.info("%s:Start next timer at sun rise", self.place)
                if self.tomato_timer is None:
                    self.tomato_timer = self.run.on_sunrise(self.timer_expired).offset(
                        timedelta(minutes=30)
                    )
                    logger.info(
                        "%s:next trigger time: %s",
                        self.place,
                        self.tomato_timer.get_next_run().strftime("%d/%m/%Y %H:%M:%S"),
                    )
                else:
                    logger.info(
                        "%s:timer already running --> next trigger time: %s",
                        self.place,
                        self.tomato_timer.get_next_run().strftime("%d/%m/%Y %H:%M:%S"),
                    )
            else:
                logger.info(
                    "%s:Set watering active for %s sec",
                    self.place,
                    TIME_FOR_WATERING_MIN,
                )
                self.activate_watering()
                duration_next_start = self.get_next_start()
                if self.tomato_timer is None:
                    self.tomato_timer = self.run.at(
                        time=timedelta(minutes=duration_next_start),
                        callback=self.timer_expired,
                    )
                    logger.info(
                        "%s:next trigger time: %s",
                        self.place,
                        self.tomato_timer.get_next_run().strftime("%d/%m/%Y %H:%M:%S"),
                    )
                else:
                    logger.info(
                        "%s:timer already running --> next trigger time: %s",
                        self.place,
                    )

    def deactivate_watering(self):
        """deactivate the watering"""
        logger.info(
            "%s:set watering: OFF for %s", self.place, self.device_name_plug_state
        )
        self.watering_state = False
        self.openhab.send_command(self.device_name_plug_state, "OFF")

    def activate_watering(self):
        """activate the watering for a given time

        Args:
            state (datetime): duration for which the pump shall be ON
        """
        logger.info(
            "%s:set watering: ON for %s", self.place, self.device_name_plug_state
        )
        self.watering_state = True
        self.openhab.send_command(self.device_name_plug_state, "ON")
        self.run.at(
            time=timedelta(minutes=TIME_FOR_WATERING_MIN),
            callback=self.deactivate_watering,
        )

    def is_dark_outside(self, sun_phase):
        """checks if it is dark outside"""
        if (
            (sun_phase == "NAUTIC_DUSK")
            | (sun_phase == "ASTRO_DUSK")
            | (sun_phase == "NIGHT")
            | (sun_phase == "ASTRO_DAWN")
            | (sun_phase == "NAUTIC_DAWN")
        ):
            return True
        else:
            return False


# Rules
MyTomatoTimer("unten")
MyTomatoTimer("oben")
