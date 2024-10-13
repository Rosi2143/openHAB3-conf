# https://habapp.readthedocs.io/en/latest/getting_started.html
import logging  # required for extended logging
from datetime import timedelta, datetime

import HABApp
from HABApp.openhab.items import NumberItem

logger = logging.getLogger("Statistic")
OH_ITEM_MAP_DAY = {
    "Gaszahler_Gas_Volume": "Gaszahler_Gas_Energy_Counter_hist_day",
    "HuaweiSolar_Meter_GridExportedEnergy": "HuaweiSolar_Statistic_DailyGridExportedEnergy",
}
OH_ITEM_MAP_MONTH = {
    "Gaszahler_Gas_Volume": "Gaszahler_Gas_Energy_Counter_hist_month",
    "HuaweiSolar_Meter_GridExportedEnergy": "HuaweiSolar_Statistic_MonthlyGridExportedEnergy",
}


class MyStatisticHandler(HABApp.Rule):
    """collect statistic data for the given items"""

    def __init__(self):
        """initialize class and calculate the first time"""
        super().__init__()

        self.run.soon(self.collect_statistic_data)
        logger.info("\n\nStatistic Handler started.")

    def get_beginning_of_last_day(self):
        """Get the beginning of the last day."""
        today = datetime.today()
        beginning_of_today = datetime(today.year, today.month, today.day)
        beginning_of_last_day = beginning_of_today - timedelta(days=1)
        logger.info(f"The beginning of the last day was: {beginning_of_last_day}")
        return beginning_of_last_day

    def get_beginning_of_last_month(self):
        """Get the beginning of the last month."""
        today = datetime.today()
        first_day_of_this_month = datetime(today.year, today.month, 1)
        last_month = first_day_of_this_month - timedelta(days=1)
        first_day_of_last_month = datetime(last_month.year, last_month.month, 1)
        number_of_days_last_month = (
            first_day_of_this_month - first_day_of_last_month
        ).days
        beginning_of_today = datetime(today.year, today.month, today.day)
        beginning_of_last_month = beginning_of_today - timedelta(
            days=number_of_days_last_month
        )
        logger.info(f"The beginning of the last month was: {beginning_of_last_month}")
        return beginning_of_last_month

    def collect_historic_data(self, item_name, last_date):
        """collect the data for the given item"""
        data = []
        if self.openhab.item_exists(item_name):
            item = NumberItem.get_item(item_name)
            data = (
                item.get_persistence_data(
                    start_time=last_date - timedelta(minutes=1),
                    end_time=last_date + timedelta(hours=23),
                )
                .get_data()
                .values()
            )
        if len(data) == 0:
            logger.warning(f"No historic data found for {item_name} at {last_date}.")
            return 0
        return list(data)[0]

    def get_value_difference(self, item_map, last_date):
        for org_element, statistic_element in item_map.items():
            value_now = 0
            value_then = 0
            if self.openhab.item_exists(org_element):
                value_now = NumberItem.get_item(org_element).get_value()
                value_then = self.collect_historic_data(org_element, last_date)
            else:
                logger.warning(f"'Now' Item {org_element} not found.")

            if self.openhab.item_exists(statistic_element):
                difference = value_now - value_then
                logger.info(
                    f"Item {statistic_element} changed since {last_date} by {difference}."
                )
                hist_item = NumberItem(statistic_element)
                hist_item.oh_post_update(difference)
            else:
                logger.warning(f"'Historic' Item {statistic_element} not found.")

    def collect_statistic_data(self):
        """collect the data for the given items"""
        today = datetime.today()
        beginning_of_last_day = self.get_beginning_of_last_day()
        beginning_of_last_month = self.get_beginning_of_last_month()
        if today.day == 1:
            logger.info("Get monthly statistic.")
            self.get_value_difference(OH_ITEM_MAP_MONTH, beginning_of_last_month)

        logger.info("Get daily statistic.")
        self.get_value_difference(OH_ITEM_MAP_DAY, beginning_of_last_day)


# Rules
MyStatisticHandler()
