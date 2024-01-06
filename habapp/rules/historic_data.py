"""calculate additional astro data for the future"""

# minimum version astral = v3.0

import logging
import datetime

import HABApp
from HABApp.openhab.items import NumberItem

logger = logging.getLogger("Historic")


class HistoricData(HABApp.Rule):
    """get additional astro data"""

    def __init__(self):
        """initialize the logger test"""
        super().__init__()

        self.run.on_every_day(
            time=datetime.time(1, 1, 1), callback=self.get_historic_data_daily
        )
        self.get_historic_data_daily()
        logger.info("started 'HistoricData'")

    def get_historic_value(self, oh_item_name, period):
        oh_item = NumberItem.get_item(oh_item_name)
        now = datetime.datetime.now()
        checktime = now - period
        last_values = oh_item.get_persistence_data(
            start_time=now, end_time=checktime
        ).get_data()
        logger.debug("%s: last values %s", oh_item_name, last_values)
        if len(last_values) > 0:
            last_value = list(last_values.values())[0]
            last_time = list(last_values.keys())[0]
            logger.info(
                "%s: last value (%s) - %s",
                oh_item_name,
                datetime.datetime.fromtimestamp(last_time),
                last_value,
            )
        else:
            last_value = None
        return last_value

    def set_number_item(self, item_name, item_value):
        """check if the item exist, (create it), set it"""
        if not self.openhab.item_exists(item_name):
            self.openhab.create_item(
                name=item_name,
                item_type="Number",
                label=item_name,
                category="f7:graph_square",
            )
        self.openhab.send_command(item_name, item_value)

    def get_historic_data_daily(self):
        """
        get historic data and set the respective item

        Args:
            event (_type_): _description_
        """

        item_set = ["MessSteckdose_Energy_Counter", "Gaszahler_Gas_Energy_Counter"]

        for oh_item_name in item_set:
            oh_item = NumberItem.get_item(oh_item_name)
            current_value = oh_item.get_value()
            logger.info("%s: current value %s", oh_item_name, current_value)

            last_value = self.get_historic_value(
                oh_item_name=oh_item_name, period=datetime.timedelta(hours=1)
            )
            if last_value is not None:
                changed_value = round(current_value - last_value, 2)
                self.set_number_item(oh_item_name + "_hist_day", changed_value)
                logger.info(
                    "%s: daily change in value = %s", oh_item_name, changed_value
                )
                if datetime.datetime.now().day == 1:
                    last_value = self.get_historic_value(
                        oh_item_name=oh_item_name, period=datetime.timedelta(days=31)
                    )
                    if last_value is not None:
                        changed_value = round(current_value - last_value, 2)
                        self.set_number_item(
                            oh_item_name + "_hist_month", changed_value
                        )
                        logger.info(
                            "%s: monthly change in value = %s",
                            oh_item_name,
                            changed_value,
                        )
                    else:
                        logger.info("%s: No historic monthly data found!", oh_item_name)
            else:
                logger.info("%s: No historic daily data found!", oh_item_name)


HistoricData()
