# https://habapp.readthedocs.io/en/latest/getting_started.html
import logging  # required for extended logging
from datetime import timedelta

import HABApp
from HABApp.openhab.items import StringItem, SwitchItem, NumberItem
from HABApp.core.events import ValueUpdateEvent, ValueUpdateEventFilter, ValueChangeEvent, ValueChangeEventFilter

logger = logging.getLogger('TomatoTimer')

TIME_FOR_WATERING_MIN = 2


class MyTomatoTimer(HABApp.Rule):
    """check when the tomatoes should get more water
       activate the pump at this time for a specified
       duration"""

    def __init__(self):
        """initialize class and calculate the first time"""
        super().__init__()

        self.run.soon(self.timer_expired)
        logger.info('Started TomatoTimer')
        self.dark_outside_item = StringItem.get_item(
            "Sonnendaten_Sonnenphase")
        dark_outside_state = self.is_dark_outside(
            self.dark_outside_item.get_value())
        logger.info("is it dark outside? --> %s", dark_outside_state)

        self.watering_active_item = SwitchItem.get_item(
            "SteckdoseAussen_Betrieb")
        watering_active_state = self.watering_active_item.get_value()
        logger.info("watering active? --> %s", watering_active_state)

        self.watering_state = (watering_active_state == "ON")
        self.timer_expired()

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
        logger.info('calculate the next start time')
        current_weather_item = StringItem.get_item(
            "openWeatherVorhersage_Wetterlage")
        current_weather_state = current_weather_item.get_value()
        logger.info(
            "openWeatherVorhersage_Wetterlage               ---   %s", current_weather_state)
        forecast_weather_item = StringItem.get_item(
            "openWeatherVorhersage_Vorhergesagte_Wetterlage")
        forecast_weather_state = forecast_weather_item.get_value()
        logger.info(
            "openWeatherVorhersage_Vorhergesagte_Wetterlage ---   %s", forecast_weather_state)

        current_rain_item = NumberItem.get_item(
            "openWeatherVorhersage_Current_PrecipitationAmount")
        current_rain_state = current_rain_item.get_value()
        logger.info(
            "openWeatherVorhersage_Current_PrecipitationAmount         ---   %0.2fmm", current_rain_state)
        forecast_rain_item = NumberItem.get_item(
            "openWeatherVorhersage_ForecastHours03_PrecipitationAmount")
        forecast_rain_state = forecast_rain_item.get_value()
        logger.info(
            "openWeatherVorhersage_ForecastHours03_PrecipitationAmount ---   %0.2fmm", forecast_rain_state)

        current_temperature_item = NumberItem.get_item(
            "openWeatherVorhersage_Current_Temperature")
        current_temperature_state = current_temperature_item.get_value()
        logger.info(
            "openWeatherVorhersage_Current_Temperature         ---   %0.2f°C", current_temperature_state)
        forecast_temperature_item = NumberItem.get_item(
            "openWeatherVorhersage_ForecastHours03_Temperature")
        forecast_temperature_state = forecast_temperature_item.get_value()
        logger.info(
            "openWeatherVorhersage_ForecastHours03_Temperature ---   %0.2f°C", forecast_temperature_state)

        current_humidity_item = NumberItem.get_item(
            "openWeatherVorhersage_Luftfeuchtigkeit")
        current_humidity_state = current_humidity_item.get_value()
        logger.info(
            "openWeatherVorhersage_Luftfeuchtigkeit               ---   %0.1f%", current_humidity_state)
        forecast_humidity_item = NumberItem.get_item(
            "openWeatherVorhersage_Vorhergesagte_Luftfeuchtigkeit")
        forecast_humidity_state = forecast_humidity_item.get_value()
        logger.info(
            "openWeatherVorhersage_Vorhergesagte_Luftfeuchtigkeit ---   %0.1f%", forecast_humidity_state)

        current_wind_item = NumberItem.get_item(
            "openWeatherVorhersage_Windgeschwindigkeit")
        current_wind_state = current_wind_item.get_value()
        logger.info(
            "openWeatherVorhersage_Windgeschwindigkeit               ---   %skm/h", current_wind_state)
        forecast_wind_item = NumberItem.get_item(
            "openWeatherVorhersage_Vorhergesagte_Windgeschwindigkeit")
        forecast_wind_state = forecast_wind_item.get_value()
        logger.info(
            "openWeatherVorhersage_Vorhergesagte_Windgeschwindigkeit ---   %skm/h", forecast_wind_state)

        current_sun_exposure_item = NumberItem.get_item(
            "Sonnendaten_DirekteStrahlung")
        current_sun_exposure_state = current_sun_exposure_item.get_value()
        logger.info(
            "Sonnendaten_DirekteStrahlung ---   %0.2flx", current_sun_exposure_state)
        current_sun_exposure_driveway_item = NumberItem.get_item(
            "LichtSensorEinfahrt_Beleuchtungsstaerke")
        current_sun_exposure_driveway_state = current_sun_exposure_driveway_item.get_value()
        logger.info(
            "LichtSensorEinfahrt_Beleuchtungsstaerke ---   %0.2flx", current_sun_exposure_driveway_state)
        current_sun_exposure_orielway_item = NumberItem.get_item(
            "LichtSensorErkerWeg_Beleuchtungsstaerke")
        current_sun_exposure_orielway_state = current_sun_exposure_orielway_item.get_value()
        logger.info(
            "LichtSensorErkerWeg_Beleuchtungsstaerke ---   %0.2flx", current_sun_exposure_orielway_state)
        current_sun_exposure_well_item = NumberItem.get_item(
            "LichtSensorBrunnen_Beleuchtungsstarke")
        current_sun_exposure_well_state = current_sun_exposure_well_item.get_value()
        logger.info(
            "LichtSensorBrunnen_Beleuchtungsstarke   ---   %0.2flx", current_sun_exposure_well_state)

        calculated_delay = 2 * 60
        logger.info("calculated delay = %s min", calculated_delay)
        return calculated_delay

    def timer_expired(self):
        """TomatoTimer expired"""

        logger.info('TomatoTimer expired')

        dark_outside_state = self.dark_outside_item.get_value()
        is_dark = self.is_dark_outside(dark_outside_state)
        if is_dark:
            logger.info("Start next timer at sun rise")
            self.run.on_sunrise(self.activate_watering)
        else:
            logger.info("Set watering active for %s sec",
                        TIME_FOR_WATERING_MIN)
            self.activate_watering()
            duration_next_start = self.get_next_start()
            self.run.at(time=timedelta(minutes=duration_next_start),
                        callback=self.activate_watering)
        # test
        self.get_next_start()

    def deactivate_watering(self):
        """deactivate the watering"""
        logger.info('set watering: OFF')
        self.watering_state = False
        self.openhab.send_command("SteckdoseAussen_Betrieb", "OFF")

    def activate_watering(self):
        """activate the watering for a given time

        Args:
            state (datetime): duration for which the pump shall be ON
        """
        logger.info('set watering: ON')
        self.watering_state = True
        self.openhab.send_command("SteckdoseAussen_Betrieb", "ON")
        self.run.at(time=timedelta(minutes=TIME_FOR_WATERING_MIN),
                    callback=self.deactivate_watering)

    def is_dark_outside(self, sun_phase):
        """checks if it is dark outside"""
        if ((sun_phase == "NAUTIC_DUSK") |
                (sun_phase == "ASTRO_DUSK") |
                (sun_phase == "NIGHT") |
                    (sun_phase == "ASTRO_DAWN") |
                    (sun_phase == "NAUTIC_DAWN")
                ):
            return True
        else:
            return False


# Rules
MyTomatoTimer()
