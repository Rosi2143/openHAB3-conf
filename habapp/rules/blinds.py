"""
This script maps the wall switches to the lights they handle.
 change to reload
"""

# Some other stuff
# see https://habapp.readthedocs.io/en/latest/advanced_usage.html#HABApp.core.events.habapp_events.RequestFileLoadEvent
# HABApp:
#   reloads on:
#    - param/blinds.yml

import logging  # required for extended logging
from datetime import timedelta, datetime
import math

import HABApp
from HABApp.openhab.items import RollershutterItem, NumberItem
from HABApp.core.events import ValueChangeEventFilter

logger = logging.getLogger("Blinds")

param_file = "blinds"
BLINDS_LIST = HABApp.DictParameter(param_file, "Blinds", default_value="")
CONDITIONS_LIST = HABApp.DictParameter(param_file, "Conditions", default_value="")


class BlindSunControl(HABApp.Rule):
    """This class handles Hue internal states."""

    def __init__(self):
        """initialize the logger test"""
        super().__init__()

        blindDict = dict(BLINDS_LIST.items())
        logger.debug(f"BLINDS_LIST: {blindDict}")
        itemNames = list(blindDict.keys())
        logger.debug(f"BLINDS_LIST.keys: {itemNames}")
        logger.debug(f"BLINDS_LIST.keys is a : {type(itemNames)}")
        logger.debug(f"len BLINDS_LIST.keys: {len(itemNames)}")

        for i in range(len(itemNames)):
            blindItemName = itemNames[i]
            blindConfig = blindDict[blindItemName]
            logger.info(
                f"BLINDS_LIST.keys[{i}]: {blindItemName} - {blindConfig['time']} / {blindConfig['level']}"
            )
            blind_item_set = RollershutterItem.get_item(
                self.get_blind_item_set_name(blindItemName)
            )
            blind_item_get = RollershutterItem.get_item(
                self.get_blind_item_get_name(blindItemName)
            )
            logger.info(
                f"Blind SetItem: {blind_item_set.name} / {blind_item_set.value}"
            )
            logger.info(
                f"Blind GetItem: {blind_item_get.name} / {blind_item_get.value}"
            )

        self.conditionOutsideTemperature = CONDITIONS_LIST["temperature"]
        logger.info(
            f"Condition - Outside temperature: {self.conditionOutsideTemperature}"
        )
        self.conditionOutsideRadiation = CONDITIONS_LIST["radiation"]
        logger.info(f"Condition - Outside radiation: {self.conditionOutsideRadiation}")
        self.conditionPreviewHours = int(CONDITIONS_LIST["preview_hours"])
        logger.info(f"Condition - Preview hours: {self.conditionPreviewHours}")

        logger.info(f"expected Temperature: {self.get_expected_temperature()}")
        logger.info(f"expected Radiation: {self.get_expected_radiation()}")

        self.run.soon(self.check_blinds)

        logger.info("Blinds rule initialized")

    def get_blind_item_set_name(self, blindItemName):
        return blindItemName + "_4_LEVEL"

    def get_blind_item_get_name(self, blindItemName):
        return blindItemName + "_3_LEVEL"

    def get_expected_temperature(self):
        expectedTemperature = (
            NumberItem.get_item("openWeatherVorhersage_Current_Temperature")
        ).get_value(0)
        if self.conditionPreviewHours > 2:
            expectedTemperature = max(
                expectedTemperature,
                (
                    NumberItem.get_item(
                        "openWeatherVorhersage_ForecastHours03_Temperature"
                    )
                ).get_value(0),
            )
        if self.conditionPreviewHours > 5:
            expectedTemperature = max(
                expectedTemperature,
                (
                    NumberItem.get_item(
                        "openWeatherVorhersage_ForecastHours06_Temperature"
                    )
                ).get_value(0),
            )
        if self.conditionPreviewHours > 8:
            expectedTemperature = max(
                expectedTemperature,
                (
                    NumberItem.get_item(
                        "openWeatherVorhersage_ForecastHours09_Temperature"
                    )
                ).get_value(0),
            )
        if self.conditionPreviewHours > 11:
            expectedTemperature = max(
                expectedTemperature,
                (
                    NumberItem.get_item(
                        "openWeatherVorhersage_ForecastHours12_Temperature"
                    )
                ).get_value(0),
            )
        if self.conditionPreviewHours > 14:
            expectedTemperature = max(
                expectedTemperature,
                (
                    NumberItem.get_item(
                        "openWeatherVorhersage_ForecastHours15_Temperature"
                    )
                ).get_value(0),
            )
        if self.conditionPreviewHours > 17:
            expectedTemperature = max(
                expectedTemperature,
                (
                    NumberItem.get_item(
                        "openWeatherVorhersage_ForecastHours18_Temperature"
                    )
                ).get_value(0),
            )
        return expectedTemperature

    def calc_expected_radiation(self, radiationLevel, cloudLevel):
        resultingRadiation = math.log10(max(1, 100 - cloudLevel)) / 2 * radiationLevel
        return resultingRadiation

    def get_expected_radiation(self):
        radiationItem = NumberItem.get_item("Sonnendaten_Gesamtstrahlung")
        currentRadiation = radiationItem.get_value(0)
        currentClouds = (
            NumberItem.get_item("openWeatherVorhersage_Bewoelkung")
        ).get_value(0)
        logger.info(
            f"currentRadiation: {currentRadiation} / currentClouds: {currentClouds}%"
        )

        resultingRadiation = self.calc_expected_radiation(
            cloudLevel=currentClouds, radiationLevel=currentRadiation
        )

        if self.conditionPreviewHours > 2:
            expectedRadiation3h = max(
                radiationItem.get_persistence_data(
                    start_time=datetime.now() - timedelta(hours=23),
                    end_time=datetime.now() - timedelta(hours=20),
                )
                .get_data()
                .values(),
                default=0,
            )
            expectedClouds3h = (
                NumberItem.get_item("openWeatherVorhersage_ForecastHours03_Bewolkung")
            ).get_value(0)

            resultingRadiation = max(
                resultingRadiation,
                self.calc_expected_radiation(
                    cloudLevel=expectedClouds3h, radiationLevel=expectedRadiation3h
                ),
            )
            logger.info(
                f"expectedRadiation3h: {expectedRadiation3h} / expectedClouds3h: {expectedClouds3h}%"
            )

        if self.conditionPreviewHours > 5:
            expectedRadiation6h = max(
                radiationItem.get_persistence_data(
                    start_time=datetime.now() - timedelta(hours=20),
                    end_time=datetime.now() - timedelta(hours=17),
                )
                .get_data()
                .values(),
                default=0,
            )
            expectedClouds6h = (
                NumberItem.get_item("openWeatherVorhersage_ForecastHours06_Bewolkung")
            ).get_value(0)
            resultingRadiation = max(
                resultingRadiation,
                self.calc_expected_radiation(
                    cloudLevel=expectedClouds6h, radiationLevel=expectedRadiation6h
                ),
            )
            logger.info(
                f"expectedRadiation6h: {expectedRadiation6h} / expectedClouds6h: {expectedClouds6h}%"
            )

        resultingRadiation = max(
            self.calc_expected_radiation(
                cloudLevel=currentClouds, radiationLevel=currentRadiation
            ),
            self.calc_expected_radiation(
                cloudLevel=expectedClouds3h, radiationLevel=expectedRadiation3h
            ),
            self.calc_expected_radiation(
                cloudLevel=expectedClouds6h, radiationLevel=expectedRadiation6h
            ),
        )
        logger.info(f"resultingRadiation: {resultingRadiation}")

        return resultingRadiation

    def get_next_check_time(self):
        blindDict = dict(BLINDS_LIST.items())
        itemNames = list(blindDict.keys())

        currentHour = datetime.now().hour
        minCheckTime = 24
        startToday = False
        logger.info(f"currentHour: {currentHour}")
        for i in range(len(itemNames)):
            blindItemName = itemNames[i]
            blindConfig = blindDict[blindItemName]
            checkTime = blindConfig["time"]
            minCheckTime = min(minCheckTime, checkTime)
            if checkTime > currentHour:
                nextCheckTime = checkTime
                startToday = True
                break

        if not startToday:
            # start tomorrow
            nextCheckTime = minCheckTime

        timmerStart = datetime.now().replace(hour=nextCheckTime, minute=0, second=10)
        if timmerStart < datetime.now():
            timmerStart += timedelta(days=1)
        logger.info(
            f"nextCheckTime: {nextCheckTime} (today: {startToday}) == {timmerStart}"
        )

        return timmerStart

    def check_blinds(self):
        logger.info("check_blinds\n")
        blindDict = dict(BLINDS_LIST.items())
        itemNames = list(blindDict.keys())

        expectedTemperature = self.get_expected_temperature()
        expectedRadiation = self.get_expected_radiation()
        logger.info(
            f"expectedTemperature: {expectedTemperature} / conditionOutsideTemperature: {self.conditionOutsideTemperature}"
        )
        logger.info(
            f"expectedRadiation: {expectedRadiation} / conditionOutsideRadiation: {self.conditionOutsideRadiation}"
        )

        if (
            expectedTemperature > self.conditionOutsideTemperature
            and expectedRadiation > self.conditionOutsideRadiation
        ):

            for i in range(len(itemNames)):
                blindItemName = itemNames[i]
                blindConfig = blindDict[blindItemName]
                currentHour = datetime.now().hour
                if blindConfig["time"] == currentHour:
                    blind_item_set = RollershutterItem.get_item(
                        self.get_blind_item_set_name(blindItemName)
                    )
                    blind_item_set.oh_send_command(blindConfig["level"])
                    logger.info(
                        f"Set blind: {blindItemName} - Level: {blindConfig['level']}"
                    )

        self.run.at(time=self.get_next_check_time(), callback=self.check_blinds)


BlindSunControl()
