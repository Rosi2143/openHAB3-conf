# https://habapp.readthedocs.io/en/latest/getting_started.html
import logging  # required for extended logging
from datetime import timedelta, datetime
import math

import HABApp
from HABApp.openhab.items import StringItem, SwitchItem, NumberItem, Thing
from HABApp.openhab.definitions import ThingStatusEnum
from HABApp.openhab.events import ThingStatusInfoChangedEvent
from HABApp.core.events import EventFilter

logger = logging.getLogger("TomatoTimer")

TIME_FOR_WATERING_MIN = 2
THING_UID_PLUG = "hue:0010:ecb5fa2c8738:25"
DEVICE_NAME_PLUG_STATE = "AussenSteckdose_Betrieb"
INITIAL_DELAY = 160

RAIN_EFFECT_FACTOR = 5
TEMPERATURE_EFFECT_BASE = 25
TEMPERATURE_EFFECT_FACTOR = 2
HUMIDITY_EFFECT_BASE = 100
HUMIDITY_EFFECT_FACTOR = 2
WIND_EFFECT_FACTOR = 5
LIGHT_EFFECT_FACTOR = 5


class MyTomatoTimer(HABApp.Rule):
    """check when the tomatoes should get more water
    activate the pump at this time for a specified
    duration"""

    def __init__(self):
        """initialize class and calculate the first time"""
        super().__init__()

        self.thing_offline_on_request = False
        self.now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        logger.info("Started TomatoTimer: %s", self.now)
        self.dark_outside_item = StringItem.get_item("Sonnendaten_Sonnenphase")
        dark_outside_state = self.is_dark_outside(self.dark_outside_item.get_value())
        logger.info("is it dark outside? --> %s", dark_outside_state)

        self.watering_active_item = SwitchItem.get_item(DEVICE_NAME_PLUG_STATE)
        watering_active_state = self.watering_active_item.get_value()
        logger.info("watering active? --> %s", watering_active_state)

        self.watering_state = watering_active_state == "ON"

        self.get_plug_thing()
        self.now = ""  # reset now to disable timer_expired workaround
        self.tomato_timer = self.run.soon(self.timer_expired)

    def thing_status_changed(self, event: ThingStatusInfoChangedEvent):
        """handle changes in plug thing status

        Args:
            event (ThingStatusInfoChangedEvent): event that lead to this change
        """
        logger.info(
            "rule fired because of %s %s --> %s",
            event.name,
            event.old_status,
            event.status,
        )
        if event.status == ThingStatusEnum.ONLINE:
            if self.thing_offline_on_request:
                logger.info("Activate plug now")
                self.thing_offline_on_request = False
                self.activate_watering()
        else:
            logger.info("%s: Details = %s", event.name, event.detail)

    def get_plug_thing(self):
        try:
            self.plug_thing = Thing.get_item(THING_UID_PLUG)
            self.plug_thing.listen_event(
                self.thing_status_changed, EventFilter(ThingStatusInfoChangedEvent)
            )
            logger.info("Thing   = %s", self.plug_thing.label)
            logger.info("Status  = %s", self.plug_thing.status)
        except ItemNotFoundException:
            logger.warning("Thing %s does not exist", DEVICE_NAME_PLUG_STATE)
            self.plug_thing = None

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
        logger.info("calculate the next start time")
        current_weather_item = StringItem.get_item("openWeatherVorhersage_Wetterlage")
        current_weather_state = current_weather_item.get_value()
        logger.info("Wetter: Wetterlage               ---   %s", current_weather_state)
        forecast_weather_item = StringItem.get_item(
            "openWeatherVorhersage_Vorhergesagte_Wetterlage"
        )
        forecast_weather_state = forecast_weather_item.get_value()
        logger.info("Wetter: Vorhergesagte_Wetterlage ---   %s", forecast_weather_state)

        current_rain_item = NumberItem.get_item(
            "openWeatherVorhersage_Current_PrecipitationAmount"
        )
        current_rain_state = current_rain_item.get_value()
        logger.info(
            "Wetter: Current_PrecipitationAmount         ---   %0.2fmm",
            current_rain_state,
        )
        forecast_rain_item = NumberItem.get_item(
            "openWeatherVorhersage_ForecastHours03_PrecipitationAmount"
        )
        forecast_rain_state = forecast_rain_item.get_value()
        logger.info(
            "Wetter: ForecastHours03_PrecipitationAmount ---   %0.2fmm",
            forecast_rain_state,
        )

        current_temperature_item = NumberItem.get_item(
            "openWeatherVorhersage_Current_Temperature"
        )
        current_temperature_state = current_temperature_item.get_value()
        logger.info(
            "Wetter: Current_Temperature         ---   %0.2f°C",
            current_temperature_state,
        )
        forecast_temperature_item = NumberItem.get_item(
            "openWeatherVorhersage_ForecastHours03_Temperature"
        )
        forecast_temperature_state = forecast_temperature_item.get_value()
        logger.info(
            "Wetter: ForecastHours03_Temperature ---   %0.2f°C",
            forecast_temperature_state,
        )

        current_humidity_item = NumberItem.get_item(
            "openWeatherVorhersage_Luftfeuchtigkeit"
        )
        current_humidity_state = current_humidity_item.get_value()
        logger.info(
            "Wetter: Luftfeuchtigkeit               ---   %0.1f%%",
            current_humidity_state,
        )
        forecast_humidity_item = NumberItem.get_item(
            "openWeatherVorhersage_Vorhergesagte_Luftfeuchtigkeit"
        )
        forecast_humidity_state = forecast_humidity_item.get_value()
        logger.info(
            "Wetter: Vorhergesagte_Luftfeuchtigkeit ---   %0.1f%%",
            forecast_humidity_state,
        )

        current_wind_item = NumberItem.get_item(
            "openWeatherVorhersage_Windgeschwindigkeit"
        )
        current_wind_state = current_wind_item.get_value()
        logger.info(
            "Wetter: Windgeschwindigkeit               ---   %skm/h", current_wind_state
        )
        forecast_wind_item = NumberItem.get_item(
            "openWeatherVorhersage_Vorhergesagte_Windgeschwindigkeit"
        )
        forecast_wind_state = forecast_wind_item.get_value()
        logger.info(
            "Wetter: Vorhergesagte_Windgeschwindigkeit ---   %skm/h",
            forecast_wind_state,
        )

        current_sun_exposure_item = NumberItem.get_item("Sonnendaten_DirekteStrahlung")
        current_sun_exposure_state = current_sun_exposure_item.get_value()
        logger.info(
            "Sonnendaten_DirekteStrahlung ---   %0.2flx", current_sun_exposure_state
        )
        current_sun_exposure_driveway_item = NumberItem.get_item(
            "LichtSensorEinfahrt_Beleuchtungsstaerke"
        )
        current_sun_exposure_driveway_state = (
            current_sun_exposure_driveway_item.get_value()
        )
        logger.info(
            "Licht: SensorEinfahrt ---   %0.2flx", current_sun_exposure_driveway_state
        )
        current_sun_exposure_orielway_item = NumberItem.get_item(
            "LichtSensorErkerWeg_Beleuchtungsstaerke"
        )
        current_sun_exposure_orielway_state = (
            current_sun_exposure_orielway_item.get_value()
        )
        logger.info(
            "Licht: SensorErkerWeg ---   %0.2flx", current_sun_exposure_orielway_state
        )
        current_sun_exposure_well_item = NumberItem.get_item(
            "LichtSensorBrunnen_Beleuchtungsstarke"
        )
        current_sun_exposure_well_state = current_sun_exposure_well_item.get_value()
        logger.info(
            "Licht: SensorBrunnen   ---   %0.2flx", current_sun_exposure_well_state
        )

        if self.plug_thing is None:
            self.get_plug_thing()

        calculated_delay = INITIAL_DELAY
        if self.plug_thing is not None:
            if self.plug_thing.status != ThingStatusEnum.ONLINE:
                logger.info(
                    "%s: Details = %s",
                    self.plug_thing.label,
                    self.plug_thing.status_detail,
                )
                logger.info("Saving ON-request")
                self.thing_offline_on_request = True
            else:
                rain_effect_min = (
                    (current_rain_state + forecast_rain_state) / 2
                ) * RAIN_EFFECT_FACTOR
                logger.info("rain_effect_min  ---   %0.1fmin", rain_effect_min)

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
                    "temperature_effect_min  ---   %0.1fmin", temperature_effect_min
                )

                humidity_effect_min = (
                    math.log2(
                        HUMIDITY_EFFECT_BASE
                        - ((current_humidity_state + forecast_humidity_state) / 2)
                    )
                    * HUMIDITY_EFFECT_FACTOR
                )
                logger.info("humidity_effect_min  ---   %0.1fmin", humidity_effect_min)

                wind_effect_min = (
                    math.log10((current_wind_state + forecast_wind_state) / 2)
                    * WIND_EFFECT_FACTOR
                )
                logger.info("wind_effect_min      ---   %0.1fmin", wind_effect_min)

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
                logger.info("light_effect_min     ---   %0.1fmin", light_effect_min)

                calculated_delay = (
                    INITIAL_DELAY
                    + rain_effect_min
                    - humidity_effect_min
                    - wind_effect_min
                    - light_effect_min
                )

        logger.info("calculated delay = %0.1fmin", calculated_delay)
        return calculated_delay

    def timer_expired(self):
        """TomatoTimer expired"""

        logger.info("TomatoTimer expired")

        self.tomato_timer = None
        # workaround as timer_expired is executed twice for on_sunrise
        now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        if now == self.now:
            logger.info("TomatoTimer expired now already")
            return
        else:
            self.now = now

        dark_outside_state = self.dark_outside_item.get_value()
        is_dark = self.is_dark_outside(dark_outside_state)
        if is_dark:
            logger.info("Start next timer at sun rise")
            if self.tomato_timer is None:
                self.tomato_timer = self.run.on_sunrise(self.timer_expired).offset(
                    timedelta(minutes=30)
                )
                logger.info(
                    "next trigger time: %s",
                    self.tomato_timer.get_next_run().strftime("%d/%m/%Y %H:%M:%S"),
                )
            else:
                logger.info(
                    "timer already running --> next trigger time: %s",
                    self.tomato_timer.get_next_run().strftime("%d/%m/%Y %H:%M:%S"),
                )
        else:
            logger.info("Set watering active for %s sec", TIME_FOR_WATERING_MIN)
            self.activate_watering()
            duration_next_start = self.get_next_start()
            if self.tomato_timer is None:
                self.tomato_timer = self.run.at(
                    time=timedelta(minutes=duration_next_start),
                    callback=self.timer_expired,
                )
                logger.info(
                    "next trigger time: %s",
                    self.tomato_timer.get_next_run().strftime("%d/%m/%Y %H:%M:%S"),
                )
            else:
                logger.info(
                    "timer already running --> next trigger time: %s",
                    self.tomato_timer.get_next_run().strftime("%d/%m/%Y %H:%M:%S"),
                )

    def deactivate_watering(self):
        """deactivate the watering"""
        logger.info("set watering: OFF")
        self.watering_state = False
        self.openhab.send_command(DEVICE_NAME_PLUG_STATE, "OFF")

    def activate_watering(self):
        """activate the watering for a given time

        Args:
            state (datetime): duration for which the pump shall be ON
        """
        logger.info("set watering: ON")
        self.watering_state = True
        self.openhab.send_command(DEVICE_NAME_PLUG_STATE, "ON")
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
MyTomatoTimer()
