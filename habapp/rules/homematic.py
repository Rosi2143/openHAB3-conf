"""
This script handles Homematic-Raspi internal states.
"""

import logging  # required for extended logging
from datetime import datetime, timedelta

import HABApp
from HABApp.openhab.items import SwitchItem, NumberItem, StringItem
from HABApp.core.events import (
    ValueChangeEvent,
    ValueChangeEventFilter,
)

logger = logging.getLogger("Homematic")


class Homematic_CCU(HABApp.Rule):
    """determine the time it took to mow the lawn"""

    def __init__(self):
        """initialize the logger test"""
        super().__init__()

        self.run.every(
            timedelta(seconds=6), timedelta(minutes=5), self.refresh_homematic_extras
        )
        logger.info("Homematic started")

        oh_item_commwd_timeout = SwitchItem.get_item("Homematic_CommWd_Timeout")
        oh_item_commwd_timeout.listen_event(
            self.homematic_comm_wd_timeout, ValueChangeEventFilter()
        )

        oh_item_comm_counter = NumberItem.get_item(
            "RaspiMaticGatewayExtras_Commcounter_Openhab"
        )
        oh_item_comm_counter.listen_event(
            self.homematic_comm_wd, ValueChangeEventFilter()
        )
        logger.info("Homematic started.")

    def refresh_homematic_extras(self):
        """send refresh to HomematicRaspi"""
        logger.debug("%s", self.refresh_homematic_extras.__name__)

        self.openhab.send_command("RaspiMaticGatewayExtras", "REFRESH")

    def homematic_comm_wd_timeout(self, event: ValueChangeEvent):
        """
        check communication

        Args:
            event (_type_): triggering event
        """
        logger.debug("%s", self.homematic_comm_wd_timeout.__name__)
        self.openhab.send_command("RaspiMaticGatewayExtras_Commcounter_Openhab", "0")
        logger.debug("Timer has executed")
        self.openhab.send_command(
            "RaspiMaticGatewayExtras_Commcounter_Error",
            NumberItem.get_item("RaspiMaticGatewayExtras_Commcounter_Error").get_value()
            + 1,
        )

        self.openhab.send_command("openHab_Binding_Restart_String", "none")
        self.run.at(timedelta(seconds=2), self.homematic_comm_wd_timeout_restart_bundle)

    def homematic_comm_wd_timeout_restart_bundle(self):
        logger.debug("%s", self.homematic_comm_wd_timeout_restart_bundle.__name__)
        self.openhab.send_command(
            "openHab_Binding_Restart_String", "org.openhab.binding.homematic"
        )

    def homematic_comm_wd(self, event: ValueChangeEvent):
        """
        check communication

        Args:
            event (_type_): triggering event
        """

        logger.debug(
            "%s : %d",
            self.homematic_comm_wd.__name__,
            NumberItem.get_item(
                "RaspiMaticGatewayExtras_Commcounter_Openhab"
            ).get_value(),
        )
        assert isinstance(event, ValueChangeEvent)
        logger.info("rule fired")

        self.openhab.send_command("Homematic_CommWd_Timeout", "OFF")


Homematic_CCU()
