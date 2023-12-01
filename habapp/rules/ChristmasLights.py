# https://habapp.readthedocs.io/en/latest/getting_started.html
import logging  # required for extended logging
from datetime import timedelta, datetime, time

import HABApp
from HABApp.openhab.items import StringItem, SwitchItem, Thing
from HABApp.openhab.definitions import ThingStatusEnum
from HABApp.openhab.events import (
    ThingStatusInfoChangedEvent,
    ItemStateUpdatedEvent,
    ItemStateUpdatedEventFilter,
)
from HABApp.core.events import EventFilter

logger = logging.getLogger("ChristmasLights")

THING_UID_PLUG = "hue:0010:ecb5fa2c8738:25"
DEVICE_NAME_PLUG_STATE = "AussenSteckdose_Betrieb"
ITEM_MOTION = "BewegungsmelderEinfahrt_MotionLong"

CHRISTMASLIGHTS_START_MONTH = 12
CHRISTMASLIGHTS_START_TIME = time(6)
CHRISTMASLIGHTS_END_TIME = time(11, 59)


class ChristmasLights(HABApp.Rule):
    """(de-)activate the christmas lights"""

    def __init__(self):
        """initialize class and calculate the first time"""
        super().__init__()

        self.thing_offline_on_request = False
        self.now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        logger.info("Started ChristmasLights: %s", self.now)
        self.dark_outside_item = StringItem.get_item("Sonnendaten_Sonnenphase")
        dark_outside_state = self.is_dark_outside(self.dark_outside_item.get_value())
        logger.info("is it dark outside? --> %s", dark_outside_state)

        self.christmaslight_active_item = SwitchItem.get_item(DEVICE_NAME_PLUG_STATE)
        christmaslight_active_state = self.christmaslight_active_item.get_value()
        logger.info("christmaslight active? --> %s", christmaslight_active_state)

        self.motiondetector_active_item = SwitchItem.get_item(ITEM_MOTION)
        motion_detect_state = self.motiondetector_active_item.get_value()
        logger.info("motion detected? --> %s", motion_detect_state)
        self.motiondetector_active_item.listen_event(
            self.motion_changed, ItemStateUpdatedEventFilter()
        )

        self.christmaslights_state = christmaslight_active_state == "ON"

        self.get_plug_thing()

        self.run.at(5, self.timer_expired)

    def timer_expired(self):
        """ChristmasLights expired"""

        logger.info("ChristmasLights expired")

        # workaround as timer_expired is executed twice for on_sunrise
        now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        if now == self.now:
            logger.info("ChristmasLights expired now already")
            return
        else:
            self.now = now

        current_month = datetime.now().month
        if current_month < CHRISTMASLIGHTS_START_MONTH:
            christmaslights_timer = self.run.on_sunrise(self.timer_expired).offset(
                timedelta(minutes=30)
            )
            logger.info(
                "no christmaslight time - next trigger time: %s",
                christmaslights_timer.get_next_run().strftime("%d/%m/%Y %H:%M:%S"),
            )
        else:
            dark_outside_state = self.dark_outside_item.get_value()
            is_dark = self.is_dark_outside(dark_outside_state)
            if not is_dark:
                logger.info("Start next timer 30min before sun set")
                christmaslights_timer = self.run.on_sunset(self.timer_expired).offset(
                    timedelta(minutes=-30)
                )
                logger.info(
                    "next trigger time: %s",
                    christmaslights_timer.get_next_run().strftime("%d/%m/%Y %H:%M:%S"),
                )
                self.deactivate_lights()
            else:
                now_time = datetime.now().time()
                if now_time > CHRISTMASLIGHTS_START_TIME and now_time < time(12):
                    logger.info("Set christmaslight active till sunrise")
                    christmaslights_timer = self.run.on_sunrise(
                        self.timer_expired
                    ).offset(timedelta(minutes=30))
                    logger.info(
                        "next trigger time: %s",
                        christmaslights_timer.get_next_run().strftime(
                            "%d/%m/%Y %H:%M:%S"
                        ),
                    )
                    self.activate_lights()
                elif now_time < CHRISTMASLIGHTS_END_TIME and now_time > time(12):
                    logger.info("Set christmaslight active till midnight")
                    christmaslights_timer = self.run.on_sunrise(
                        self.timer_expired
                    ).offset(timedelta(minutes=30))
                    logger.info(
                        "next trigger time: %s",
                        christmaslights_timer.get_next_run().strftime(
                            "%d/%m/%Y %H:%M:%S"
                        ),
                    )
                    self.activate_lights()
                elif (
                    now_time > CHRISTMASLIGHTS_END_TIME
                    or now_time < CHRISTMASLIGHTS_START_TIME
                ):
                    logger.info("Set christmaslight inactive till start-time")
                    christmaslights_timer = self.run.at(
                        time=CHRISTMASLIGHTS_START_TIME,
                        callback=self.timer_expired,
                    )
                    logger.info(
                        "next trigger time: %s",
                        christmaslights_timer.get_next_run().strftime(
                            "%d/%m/%Y %H:%M:%S"
                        ),
                    )
                    self.deactivate_lights()
                else:
                    christmaslights_timer = self.run.at(
                        time=timedelta(minutes=duration_next_start),
                        callback=self.timer_expired,
                    )
                    logger.info(
                        "next trigger time: %s",
                        christmaslights_timer.get_next_run().strftime(
                            "%d/%m/%Y %H:%M:%S"
                        ),
                    )
                    self.activate_lights()

    def thing_status_changed(self, event: ThingStatusInfoChangedEvent):
        """handle changes in plug thing status

        Args:
            event (ThingStatusInfoChangedEvent): event that lead to this change
        """
        logger.info(
            "rule fired because of %s %s --> %s",
            event.name,
            event.old_status,
            event.status,
        )
        if event.status == ThingStatusEnum.ONLINE:
            if self.thing_offline_on_request:
                logger.info("Activate plug now")
                self.thing_offline_on_request = False
                self.activate_lights()
        else:
            logger.info("%s: Details = %s", event.name, event.detail)

    def get_plug_thing(self):
        try:
            self.plug_thing = Thing.get_item(THING_UID_PLUG)
            self.plug_thing.listen_event(
                self.thing_status_changed, EventFilter(ThingStatusInfoChangedEvent)
            )
            logger.info("Thing   = %s", self.plug_thing.label)
            logger.info("Status  = %s", self.plug_thing.status)
        except ItemNotFoundException:
            logger.warning("Thing %s does not exist", DEVICE_NAME_PLUG_STATE)
            self.plug_thing = None

    def deactivate_lights(self, change_state_request=True):
        """deactivate the christmaslight"""
        logger.info("set christmaslight: OFF")
        if change_state_request:
            self.christmaslights_state = False
        self.openhab.send_command(DEVICE_NAME_PLUG_STATE, "OFF")

    def activate_lights(self, change_state_request=True):
        """activate the christmaslight for a given time

        Args:
            state (datetime): duration for which the pump shall be ON
        """
        logger.info("set christmaslight: ON")
        if change_state_request:
            self.christmaslights_state = True
        self.openhab.send_command(DEVICE_NAME_PLUG_STATE, "ON")

    def is_dark_outside(self, sun_phase):
        """checks if it is dark outside"""
        if (
            (sun_phase == "NAUTIC_DUSK")
            | (sun_phase == "ASTRO_DUSK")
            | (sun_phase == "NIGHT")
            | (sun_phase == "ASTRO_DAWN")
            | (sun_phase == "NAUTIC_DAWN")
        ):
            logger.info("It's %s and dark", sun_phase)
            return True
        else:
            logger.info("It's %s and not dark", sun_phase)
            return False

    def motion_changed(self, event):
        """checks if it is dark outside"""
        assert isinstance(event, ItemStateUpdatedEvent)

        if str(event.value) == "ON":
            self.activate_lights(False)
        else:
            if not self.christmaslights_state:
                self.deactivate_lights(False)


# Rules
ChristmasLights()
