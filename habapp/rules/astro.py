"""This script handles event triggers of the astro events."""

import logging
import inspect

import HABApp
from HABApp.openhab.items import SwitchItem, ContactItem, NumberItem
from HABApp.openhab import transformations

logger = logging.getLogger("Astro")

INDEGO_MAP = transformations.map[
    "indego.map"
]  # load the transformation, can be used anywhere


class AstroInfo(HABApp.Rule):
    """get astro data"""

    def __init__(self):
        """initialize the logger test"""
        super().__init__()

        self.run.on_sunrise(self.sunrise)
        self.run.on_sunset(self.sunset)
        self.run.on_sun_dusk(self.sundusk)

        logger.info("started 'AstroInfo'")

    def func_name(self) -> str:
        return inspect.stack()[1].function

    def sunrise(self):
        """
        handle sunrise start event

        Args:
            event (_type_): triggering event
        """
        logger.info(self.func_name())

        logger.info("Hue de-activate NightLight")
        self.openhab.send_command("Hue_Zone_Garten_Betrieb", "OFF")
        self.openhab.send_command("IstTag", "ON")

    def sunset(self):
        """
        handle sunset start event

        Args:
            event (_type_): triggering event
        """
        logger.info(self.func_name())

        if SwitchItem.get_item("GartenLichtAutomatik").get_value() == "ON":
            logger.info("Hue activate NightLight")
            self.openhab.send_command("Hue_Zone_Garten_Betrieb", "ON")
            self.openhab.send_command("Hue_Zone_Garten_Zone", "Nachtlicht")

        self.openhab.send_command("IstTag", "OFF")

    def sundusk(self):
        """
        handle astroDusk (+20min) start event
        Args:
            event (_type_): triggering event
        """
        logger.info(self.func_name())

        if ContactItem.get_item("TuerWaschkuecheTerrasse_OpenState").get_value() == "OPEN":
            self.openhab.send_command("SchlossWaschkueche_Fehler", "ON")
            logger.error("cannot lock the door -- as it is open")
        else:
            self.openhab.send_command("SchlossWaschkueche_LockTargetLevel", "LOCKED")

        if (
            NumberItem.get_item("Bosch_Indego_Zustand_numerisch").get_value()
            == INDEGO_MAP["mow"]
        ):
            self.openhab.send_command(
                "Bosch_Indego_Zustand_numerisch", INDEGO_MAP["return_to_dock"]
            )
            logger.error("Indego still mowing --> send home")
        else:
            logger.info("Indego not mowing --> OK")


AstroInfo()
