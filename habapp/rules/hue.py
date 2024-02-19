"""
This script handles constant offline problem of hue network.
"""

import logging  # required for extended logging
from datetime import timedelta

import HABApp
from HABApp.openhab.items import SwitchItem, GroupItem
from HABApp.core.events import ValueChangeEvent, ValueChangeEventFilter

logger = logging.getLogger("Hue")


class Hue(HABApp.Rule):
    """This class handles Hue internal states."""

    def __init__(self):
        """initialize the logger test"""
        super().__init__()

        oh_item_erkerweg_motion = SwitchItem.get_item("BewegungsmelderErkerweg_Motion")
        oh_item_erkerweg_motion.listen_event(
            self.motion_long, ValueChangeEventFilter(value="ON")
        )
        oh_item_einfahrt_motion = SwitchItem.get_item("BewegungsmelderEinfahrt_Motion")
        oh_item_einfahrt_motion.listen_event(
            self.motion_long, ValueChangeEventFilter(value="ON")
        )
        oh_item_brunnen_motion = SwitchItem.get_item("BewegungsmelderBrunnen_Bewegung")
        oh_item_brunnen_motion.listen_event(
            self.motion_long, ValueChangeEventFilter(value="ON")
        )

        self.run.every(
            timedelta(seconds=16),
            timedelta(minutes=5),
            self.offline_handler,
            event=None,
        )

        logger.info("Hue started.")

    def motion_long(self, event):
        """
        start timeout for motion detect

        Args:
            event (_type_): triggering event
        """
        logger.info(
            "rule fired because of %s %s --> %s",
            event.name,
            event.old_value,
            event.value,
        )

        self.openhab.send_command(event.name + "Long", "ON")

    def offline_handler(self, event):
        """
        handle offline problems of outside lights

        Args:
            event (_type_): triggering event
        """

        EinfahrtDunkel = SwitchItem.get_item("LichtSensorEinfahrt_Dunkel").get_value()
        EinfahrtBewegung = SwitchItem.get_item(
            "BewegungsmelderErkerweg_MotionLong"
        ).get_value()
        EinfahrtMax = int(GroupItem.get_item("Hue_Raum_Einfahrt_Max").get_value())
        EinfahrtMin = int(GroupItem.get_item("Hue_Raum_Einfahrt_Min").get_value())

        logger.info(
            "rule fired: Einfahrt: Dunkel %s; Bewegung %s; Min %s; Max %s",
            EinfahrtDunkel,
            EinfahrtBewegung,
            EinfahrtMin,
            EinfahrtMax,
        )

        if (EinfahrtMax - EinfahrtMin) > 5:
            logger.error("Diff in EinfahrtLights = %d", (EinfahrtMax - EinfahrtMin))
        if EinfahrtDunkel == "ON":
            self.openhab.send_command("Hue_Raum_Einfahrt_Betrieb", "ON")
            if EinfahrtBewegung == "ON":
                logger.info("EinfahrtLights activate Light")
                self.openhab.send_command("Hue_Raum_Einfahrt_Szene", "Konzentrieren")
            else:
                logger.info("EinfahrtLights de-activate Light")
                self.openhab.send_command("Hue_Raum_Einfahrt_Szene", "Nachtlicht")
        else:
            self.openhab.send_command("Hue_Raum_Einfahrt_Betrieb", "OFF")

        ErkerWegDunkel = SwitchItem.get_item("LichtSensorErkerWeg_Dunkel").get_value()
        ErkerWegBewegung = SwitchItem.get_item(
            "BewegungsmelderErkerweg_MotionLong"
        ).get_value()
        ErkerWegMax = int(GroupItem.get_item("Hue_Raum_Erkerweg_Max").get_value())
        ErkerWegMin = int(GroupItem.get_item("Hue_Raum_Erkerweg_Min").get_value())

        logger.info(
            "rule fired: ErkerWeg: Dunkel %s; Bewegung %s; Min %s; Max %s",
            ErkerWegDunkel,
            ErkerWegBewegung,
            ErkerWegMin,
            ErkerWegMax,
        )

        if (ErkerWegMax - ErkerWegMin) > 5:
            logger.error("Diff in ErkerWegLights = %d", (ErkerWegMax - ErkerWegMin))
        if ErkerWegDunkel == "ON":
            self.openhab.send_command("Hue_Raum_Erkerweg_Betrieb", "ON")
            if ErkerWegBewegung == "ON":
                logger.info("ErkerWegLights activate Light")
                self.openhab.send_command("Hue_Raum_Erkerweg_Szene", "Konzentrieren")
            else:
                logger.info("ErkerWegLights de-activate Light")
                self.openhab.send_command("Hue_Raum_Erkerweg_Szene", "Nachtlicht")
        else:
            self.openhab.send_command("Hue_Raum_Erkerweg_Betrieb", "OFF")

        BrunnenDunkel = SwitchItem.get_item("LichtSensorBrunnen_Dunkel").get_value()
        BrunnenBewegung = SwitchItem.get_item(
            "BewegungsmelderBrunnen_BewegungLong"
        ).get_value()
        BrunnenMax = int(GroupItem.get_item("Hue_Raum_Brunnen_Max").get_value())
        BrunnenMin = int(GroupItem.get_item("Hue_Raum_Brunnen_Min").get_value())

        logger.info(
            "rule fired: Brunnen : Dunkel %s; Bewegung %s; Min %s; Max %s",
            BrunnenDunkel,
            BrunnenBewegung,
            BrunnenMin,
            BrunnenMax,
        )

        if (BrunnenMax - BrunnenMin) > 5:
            logger.error("Diff in BrunnenLights = %d", (BrunnenMax - BrunnenMin))
        if BrunnenDunkel == "ON":
            self.openhab.send_command("Hue_Raum_Erkerweg_Betrieb", "ON")
            if BrunnenBewegung == "ON":
                logger.info("BrunnenLights activate Light")
                self.openhab.send_command("Hue_Raum_Brunnen_Szene", "Konzentrieren")
            else:
                logger.info("BrunnenLights de-activate Light")
                self.openhab.send_command("Hue_Raum_Brunnen_Szene", "Nachtlicht")
        else:
            self.openhab.send_command("Hue_Raum_Erkerweg_Betrieb", "OFF")


Hue()
