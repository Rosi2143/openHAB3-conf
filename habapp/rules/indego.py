import logging  # required for extended logging
from datetime import datetime, timedelta
import time
import sys

import HABApp
from HABApp.openhab.items import StringItem
from HABApp.core.events import (
    ValueChangeEvent,
    ValueChangeEventFilter,
)

logger = logging.getLogger("Indego")

OH_CONF = "/etc/openhab/"
OH_ITEM_INDEGO_STATUS_TEXT = "Bosch_Indego_StatusText"
OH_ITEM_INDEGO_MOW_TIME = "Bosch_Indego_Last_MowTime"
OH_ITEM_INDEGO_PAUSE_TIME = "Bosch_Indego_Last_PauseTime"

sys.path.append(OH_CONF + "habapp/rules/")
from statemachines.IndegoStatemachine import IndegoStatemachine

indego_state_machine = IndegoStatemachine(name="Indego_S+500", logger=logger)


class Indego(HABApp.Rule):
    """determine the time it took to mow the lawn"""

    def __init__(self):
        """initialize the logger test"""
        super().__init__()

        self.statusText = StringItem.get_item(OH_ITEM_INDEGO_STATUS_TEXT)
        self.statusText.listen_event(self.status_changes, ValueChangeEventFilter())
        logger.info("Indego started. Current state = %s", self.statusText.value)

        self.startTimeMow = datetime.now()
        self.mowingTime = 0
        self.startTimePause = datetime.now()
        self.pauseTime = timedelta(0)
        self.status = indego_state_machine.STATUS_UNKNOWN
        self.run.soon(
            self.status_changes,
            ValueChangeEvent(name="start-up", value="none", old_value="none"),
        )

    def status_changes(self, event: ValueChangeEvent):
        """
        send event to DoorLock statemachine if ReportedLock changes
        Args:
            event (_type_): any ReportedLock item
        """
        logger.info(
            "rule fired because of %s %s --> %s",
            event.name,
            event.old_value,
            event.value,
        )

        self.statusText = str(
            StringItem.get_item(OH_ITEM_INDEGO_STATUS_TEXT).get_value()
        )

        indego_state_machine.set_reported_state(self.statusText)

        if (
            indego_state_machine.current_state.name.lower()
            != indego_state_machine.STATUS_DOCK
        ):
            self.run.soon(self.item_updater)
        else:
            logger.info("Indego is docked - timer not started")

    def item_updater(self):
        """run a timer if required and update the indego action times"""
        logger.info("Update times")
        mowtime, pausetime = indego_state_machine.get_action_timer()
        self.openhab.send_command(OH_ITEM_INDEGO_MOW_TIME, mowtime)
        self.openhab.send_command(OH_ITEM_INDEGO_PAUSE_TIME, pausetime)
        if (
            indego_state_machine.current_state.name.lower()
            != indego_state_machine.STATUS_DOCK
        ):
            logger.info("Restart timer")
            self.run.at(time=timedelta(seconds=5), callback=self.item_updater)


Indego()
