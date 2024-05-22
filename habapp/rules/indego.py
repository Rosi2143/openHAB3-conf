import logging  # required for extended logging
from datetime import datetime, timedelta
import os
import sys

import HABApp
from HABApp.openhab.items import StringItem
from HABApp.core.events import (
    ValueChangeEvent,
    ValueChangeEventFilter,
)

logger = logging.getLogger("Indego")

param_file = "openhab"
OH_CONF = HABApp.DictParameter(param_file, "OH_Directories", default_value="")[
    "OPENHAB_CONF"
]
HABAPP_RULES = HABApp.DictParameter(param_file, "HABAPP_Directories", default_value="")[
    "HABAPP_RULES"
]

OH_ITEM_INDEGO_STATUS_TEXT = "Bosch_Indego_StatusText"
OH_ITEM_INDEGO_MOW_TIME = "Bosch_Indego_Last_MowTime"
OH_ITEM_INDEGO_PAUSE_TIME = "Bosch_Indego_Last_PauseTime"

sys.path.append(os.path.join(OH_CONF, HABAPP_RULES))
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
        self.next_timer_job = self.run.soon(
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
            self.next_timer_job = self.run.soon(self.item_updater)
        else:
            logger.info("Indego is docked - timer not started")

    def get_valid_time_format(self, time_in):
        return "{:02}:{:02}:{:02}".format(
            int(time_in.seconds / 3600),
            int((time_in.seconds / 60) % 60),
            int(time_in.seconds % 60),
        )

    def item_updater(self):
        """run a timer if required and update the indego action times"""
        logger.info("Update times")
        mowtime, pausetime = indego_state_machine.get_action_timer()
        self.openhab.send_command(
            OH_ITEM_INDEGO_MOW_TIME, self.get_valid_time_format(mowtime)
        )
        logger.info("MowTime  : %s", self.get_valid_time_format(mowtime))
        self.openhab.send_command(
            OH_ITEM_INDEGO_PAUSE_TIME, self.get_valid_time_format(pausetime)
        )
        logger.info("PauseTime: %s", self.get_valid_time_format(pausetime))
        if (
            indego_state_machine.current_state.name.lower()
            != indego_state_machine.STATUS_DOCK
        ):
            logger.info("Restart timer")
            if self.next_timer_job.remaining() != None:
                self.next_timer_job.cancel()
            self.run.at(time=timedelta(seconds=10), callback=self.item_updater)


Indego()
