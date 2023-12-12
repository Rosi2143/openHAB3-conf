"""make lights follow motion detector state"""

# log:set INFO jsr223.jython.mp3_player_mode
# minimum version python-statemachine = 1.0.3
import logging  # required for extended logging

from datetime import datetime

import HABApp
from HABApp.core.events import ValueChangeEvent, ValueChangeEventFilter
from HABApp.openhab.items import GroupItem

log = logging.getLogger("MotionDetector")

OH_CONF = "/etc/openhab/"


class motion_detector(HABApp.Rule):
    """control lights by motion detector state"""

    def __init__(self):
        """initialize the logger test"""
        super().__init__()

        motion_detector_group_item = GroupItem.get_item("gBewegungsmelder_MotionState")
        for i in motion_detector_group_item.members:
            i.listen_event(self.motion_detector_group_change, ValueChangeEventFilter())
        log.info("motion detector started")

    def motion_detector_group_change(self, event: ValueChangeEvent):
        """handle the change of a state"""

        log.info(
            "##############################\nrule fired because of %s %s --> %s",
            event.name,
            event.old_value,
            event.value,
        )

        light_item_name_map = {"LichtFlur_State": "LichtFlurKeller_State"}

        light_item_name = "Licht" + str(event.name).replace(
            "Bewegungsmelder", ""
        ).replace("_MotionState", "_State")
        if light_item_name in light_item_name_map:
            light_item_name = light_item_name_map[light_item_name]

        if self.check_time_restriction(event.name):
            self.openhab.send_command(light_item_name, str(event.value))

    def check_time_restriction(self, itemName):
        motionDetectorItem = self.openhab.get_item(itemName)
        metaData = motionDetectorItem.metadata
        log.info("%s: --> %s:%s", itemName, motionDetectorItem.label, metaData)

        timeRestraint = metaData.get("TimeRestraints")
        if timeRestraint is None:
            log.info("no extended motion detector")
            return True
        log.info("found metadata for time restriction %s", timeRestraint)

        timeConfig = timeRestraint.get("config")
        if timeConfig is None:
            log.info("no extended motion detector")
            return True
        log.info("found metadata for time Config %s", timeConfig)

        configCount = 1
        while (timeConfig.get(f"ON_{configCount}") is not None) and (
            timeConfig.get(f"OFF_{configCount}") is not None
        ):
            configOn = timeConfig.get(f"ON_{configCount}")
            configOff = timeConfig.get(f"OFF_{configCount}")
            log.info(
                "found metadata for time %s %s -- %s", configCount, configOn, configOff
            )
            returnvalue = False
            if not self.is_time_between(configOn, configOff):
                log.info("currently disabled")
            else:
                log.info("currently enabled")
                returnvalue = True
            configCount = configCount + 1

        log.info("check_time_restriction = %s", returnvalue)
        return returnvalue

    def is_time_between(self, begin_time_str, end_time_str):
        # If check time is not given, default to current UTC time
        timeFormat24h = "%H:%M:%S"
        begin_time = datetime.strptime(begin_time_str, timeFormat24h).time()
        end_time = datetime.strptime(end_time_str, timeFormat24h).time()
        check_time = datetime.now().time()
        if begin_time < end_time:
            return check_time >= begin_time and check_time <= end_time
        else:  # crosses midnight
            return check_time >= begin_time or check_time <= end_time


motion_detector()
