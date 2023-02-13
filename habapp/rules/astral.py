"""calculate additional astro data for the future"""

# minimum version astral = v3.0

from astral.sun import sun
from astral import LocationInfo

import logging
import datetime
import zoneinfo

import HABApp
from HABApp.core.items import Item
from HABApp.core.events import ValueUpdateEvent, ValueUpdateEventFilter, ValueChangeEvent, ValueChangeEventFilter

logger = logging.getLogger('Astral')


class AstralInfo(HABApp.Rule):
    """get additional astro data"""

    def __init__(self):
        """initialize the logger test"""
        super().__init__()

        self.run.on_every_day(
            time=datetime.time(1, 2, 3),
            callback=self.get_additional_astro_data)
        self.get_additional_astro_data()
        logger.info("started 'AstralInfo'")

    def set_date_item(self, item_name, item_value, group_name):
        """check if the item exist, (create it), set it
        """
        if not self.openhab.item_exists(item_name):
            self.openhab.create_item(name=item_name, item_type="DateTime", label=item_name,
                                     category="calendar", groups=[group_name])
        self.openhab.send_command(item_name, item_value)

    def get_additional_astro_data(self):
        """
        get astro data of tomorrow and beyond

        Args:
            event (_type_): _description_
        """

        holle = LocationInfo("Holle", "Germany", "Europe/Berlin", 52.09, 10.16)
        timezone = zoneinfo.ZoneInfo("Europe/Berlin")
        local_sun_tomorrow = sun(holle.observer, date=datetime.date.today(
        ) + datetime.timedelta(days=1), tzinfo=timezone)
        local_sun_day2 = sun(holle.observer, date=datetime.date.today(
        ) + datetime.timedelta(days=2), tzinfo=timezone)

        logger.info("tomorrow sunrise: %s", str(
            local_sun_tomorrow["sunrise"]))
        logger.info("tomorrow sunset : %s", str(local_sun_tomorrow["sunset"]))
        logger.info("2-days sunrise: %s", str(local_sun_day2["sunrise"]))
        logger.info("2-days sunset : %s", str(local_sun_day2["sunset"]))

        self.set_date_item("openWeatherVorhersage_ForecastTomorrow_Sunrise",
                           local_sun_tomorrow["sunrise"], "Sonnendaten")
        self.set_date_item("openWeatherVorhersage_ForecastTomorrow_Sunset",
                           local_sun_tomorrow["sunset"], "Sonnendaten")

        self.set_date_item("openWeatherVorhersage_ForecastDay2_Sunrise",
                           local_sun_day2["sunrise"], "Sonnendaten")
        self.set_date_item("openWeatherVorhersage_ForecastDay2_Sunset",
                           local_sun_day2["sunset"], "Sonnendaten")


AstralInfo()
