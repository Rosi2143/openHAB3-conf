import logging  # required for extended logging
from datetime import datetime, timedelta
import time

import HABApp
from HABApp.openhab.items import StringItem
from HABApp.core.events import (
    ValueChangeEvent,
    ValueChangeEventFilter,
)

logger = logging.getLogger("Indego")

INDEGO_STATUS_MOW = "mow"
INDEGO_STATUS_PAUSE = "pause"
INDEGO_STATUS_DOCK = "dock"
INDEGO_STATUS_UNKNOWN = "unknown"

TESTING = False


class Indego(HABApp.Rule):
    """determine the time it took to mow the lawn"""

    def __init__(self):
        """initialize the logger test"""
        super().__init__()

        self.statusText = StringItem.get_item("Bosch_Indego_StatusText")
        self.statusText.listen_event(self.status_changes, ValueChangeEventFilter())
        logger.info("Indego started. Current state = %s", self.statusText)

        self.startTimeMow = datetime.now()
        self.mowingTime = 0
        self.startTimePause = datetime.now()
        self.pauseTime = timedelta(0)
        self.status = INDEGO_STATUS_UNKNOWN
        self.run.soon(
            self.status_changes,
            ValueChangeEvent(name="start-up", value="none", old_value="none"),
        )

        if TESTING:
            self.run.at(time=timedelta(seconds=5), callback=self.testing)

    def testing(self):
        ## Test section
        logger.info("#############")
        logger.info("Starting Test")
        logger.info("#############")
        self.eval_new_status(self.eval_status_update("Border cut"))
        time.sleep(5)
        self.eval_new_status(self.eval_status_update("Mowing randomly"))
        time.sleep(5)
        self.eval_new_status(self.eval_status_update("Idle in Lawn"))
        time.sleep(5)
        self.eval_new_status(self.eval_status_update("Mowing randomly"))
        time.sleep(5)
        self.eval_new_status(self.eval_status_update("Relocalising"))
        time.sleep(5)
        self.eval_new_status(self.eval_status_update("Mowing"))
        time.sleep(5)
        self.eval_new_status(self.eval_status_update("Returning to Dock - Battery low"))
        time.sleep(5)
        self.eval_new_status(self.eval_status_update("SpotMow"))
        time.sleep(5)
        self.eval_new_status(self.eval_status_update("Paused"))
        time.sleep(5)
        self.eval_new_status(self.eval_status_update("Mowing"))
        time.sleep(5)
        self.eval_new_status(
            self.eval_status_update("Returning to Dock - Lawn complete")
        )
        time.sleep(5)
        self.eval_new_status(self.eval_status_update("Docked"))
        time.sleep(5)
        self.eval_new_status(self.eval_status_update("swfsdfwe"))
        time.sleep(5)
        self.eval_new_status(self.eval_status_update("Docked"))
        logger.info("###########")
        logger.info("Ending Test")
        logger.info("###########")

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

        self.statusText = str(StringItem.get_item("Bosch_Indego_StatusText"))

        newStatus = self.eval_status_update(self.statusText)
        self.status = self.eval_new_status(newStatus)

    def eval_status_update(self, statusUpdate):
        if (
            ("Mowing" in statusUpdate)
            or ("Border cut" in statusUpdate)
            or ("Leaving" in statusUpdate)
            or ("SpotMow" in statusUpdate)
        ):
            newStatus = INDEGO_STATUS_MOW
        elif (
            ("Battery low" in statusUpdate)
            or ("Idle" in statusUpdate)
            or ("Paused" in statusUpdate)
            or ("Relocalising" in statusUpdate)
            or ("Returning" in statusUpdate)
        ):
            if self.status == INDEGO_STATUS_MOW:
                newStatus = INDEGO_STATUS_PAUSE
            else:
                newStatus = INDEGO_STATUS_DOCK
        elif ("Charging" in statusUpdate) or ("Docked" in statusUpdate):
            newStatus = INDEGO_STATUS_DOCK
        else:
            newStatus = INDEGO_STATUS_UNKNOWN
            logger.error("Unknown state %s", statusUpdate)

        logger.info("NewStatus = %s", newStatus)
        return newStatus

    def eval_new_status(self, newStatus):
        if newStatus != self.status:
            if (self.status == INDEGO_STATUS_DOCK) and (newStatus == INDEGO_STATUS_MOW):
                self.startTimeMow = datetime.now()
            elif (self.status == INDEGO_STATUS_MOW) and (
                newStatus == INDEGO_STATUS_PAUSE
            ):
                self.startTimePause = datetime.now()
            elif (self.status == INDEGO_STATUS_PAUSE) and (
                newStatus == INDEGO_STATUS_MOW
            ):
                self.pauseTime = self.pauseTime + (datetime.now() - self.startTimePause)
                logger.info("Pause stopped after %s", self.format_time(self.pauseTime))
            elif (
                (self.status == INDEGO_STATUS_MOW)
                or (self.status == INDEGO_STATUS_PAUSE)
            ) and (newStatus == INDEGO_STATUS_DOCK):
                self.mowingTime = datetime.now() - self.startTimeMow - self.pauseTime
                logger.info("###########################################")
                logger.info("Mowing complete")
                logger.info(
                    "overall time = %s",
                    self.format_time(datetime.now() - self.startTimeMow),
                )
                logger.info("Mowing time  = %s", self.format_time(self.mowingTime))
                logger.info("Pause time   = %s", self.format_time(self.pauseTime))
                logger.info("###########################################")
                self.pauseTime = timedelta(0)
            else:
                if (newStatus != INDEGO_STATUS_UNKNOWN) and (
                    self.status != INDEGO_STATUS_UNKNOWN
                ):
                    logger.error("Unknown combination")

            logger.debug("oldStatus = %s --> newStatus = %s", self.status, newStatus)
            self.status = newStatus
        else:
            logger.debug("status = %s", self.status)

        return self.status

    def format_time(self, in_time):
        return str(in_time).split(".")[0]


Indego()
