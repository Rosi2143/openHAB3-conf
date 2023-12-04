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

THING_UID_BASE = "hue:0010:ecb5fa2c8738:"
THING_UID_OUTDOOR_PLUG = f"{THING_UID_BASE}25"
DEVICE_NAME_OUTDOOR_PLUG_STATE = "AussenSteckdose_Betrieb"

THING_UID_CANDLE_ARCH_PLUG = f"{THING_UID_BASE}19"
DEVICE_NAME_CANDLE_ARCH_PLUG_STATE = "SteckdoseSchwibbogen_Betrieb"

THING_UID_TREE_IN_CORRIDOR_PLUG = f"{THING_UID_BASE}20"
DEVICE_NAME_TREE_IN_CORRIDOR_PLUG_STATE = "SteckdoseBaumImFlur_Betrieb"

ITEM_MOTION = "BewegungsmelderEinfahrt_MotionLong"

CHRISTMASLIGHTS_START_MONTH = 12
CHRISTMASLIGHTS_START_TIME = time(6)
CHRISTMASLIGHTS_NOON_TIME = time(12)
CHRISTMASLIGHTS_END_TIME = time(23, 59)


class ChristmasLights(HABApp.Rule):
    """(de-)activate the christmas lights"""

    def __init__(self):
        """initialize class and calculate the first time"""
        super().__init__()

        self.thing_offline_on_request = False
        self.now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        logger.info("Started ChristmasLights: %s", self.now)
        self.dark_outside_item = StringItem.get_item("Sonnendaten_Sonnenphase")
        self.dark_outside_state = self.is_dark_outside(
            self.dark_outside_item.get_value()
        )
        logger.info("is it dark outside? --> %s", self.dark_outside_state)
        self.dark_outside_item.listen_event(
            self.sun_state_changed, ItemStateUpdatedEventFilter()
        )

        self.christmaslight_active_item = SwitchItem.get_item(
            DEVICE_NAME_OUTDOOR_PLUG_STATE
        )
        christmaslight_active_state = self.christmaslight_active_item.get_value()
        logger.info("christmaslight active? --> %s", christmaslight_active_state)

        self.motiondetector_active_item = SwitchItem.get_item(ITEM_MOTION)
        motion_detect_state = self.motiondetector_active_item.get_value()
        logger.info("motion detected? --> %s", motion_detect_state)
        self.motiondetector_active_item.listen_event(
            self.motion_changed, ItemStateUpdatedEventFilter()
        )

        self.christmaslights_state = christmaslight_active_state == "ON"

        self.get_plug_things()

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
                logger.info("Start at sun set")
                self.set_lights(state="OFF")
            else:
                now_time = datetime.now().time()
                if (
                    now_time > CHRISTMASLIGHTS_START_TIME
                    and now_time < CHRISTMASLIGHTS_NOON_TIME
                ):
                    logger.info("Set christmaslight active till sunrise")
                    self.set_lights(state="ON")
                elif (
                    now_time > CHRISTMASLIGHTS_NOON_TIME
                    and now_time < CHRISTMASLIGHTS_END_TIME
                ):
                    logger.info("Set christmaslight active till midnight")
                    christmaslights_timer = self.run.at(
                        time=CHRISTMASLIGHTS_END_TIME, callback=self.timer_expired
                    )
                    logger.info(
                        "next trigger time: %s",
                        christmaslights_timer.get_next_run().strftime(
                            "%d/%m/%Y %H:%M:%S"
                        ),
                    )
                    self.set_lights(state="ON")
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
                    self.set_lights(state="OFF")
                else:
                    logger.error(
                        "unknown condition: time %s, sunstate %s",
                        now_time.strftime("%d/%m/%Y %H:%M:%S"),
                        self.is_dark_outside(self.dark_outside_item.get_value()),
                    )

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
                self.set_lights(state="ON")
        else:
            logger.info("%s: Details = %s", event.name, event.detail)

    def get_plug_things(self):
        try:
            self.outdoor_plug_thing = Thing.get_item(THING_UID_OUTDOOR_PLUG)
            self.outdoor_plug_thing.listen_event(
                self.thing_status_changed, EventFilter(ThingStatusInfoChangedEvent)
            )
            logger.info("Thing   = %s", self.outdoor_plug_thing.label)
            logger.info("Status  = %s", self.outdoor_plug_thing.status)
        except ItemNotFoundException:
            logger.warning("Thing %s does not exist", DEVICE_NAME_OUTDOOR_PLUG_STATE)
            self.outdoor_plug_thing = None

        try:
            self.candlearch_plug_thing = Thing.get_item(THING_UID_CANDLE_ARCH_PLUG)
            self.candlearch_plug_thing.listen_event(
                self.thing_status_changed, EventFilter(ThingStatusInfoChangedEvent)
            )
            logger.info("Thing   = %s", self.candlearch_plug_thing.label)
            logger.info("Status  = %s", self.candlearch_plug_thing.status)
        except ItemNotFoundException:
            logger.warning("Thing %s does not exist", DEVICE_NAME_OUTDOOR_PLUG_STATE)
            self.candlearch_plug_thing = None

        try:
            self.treeincorridor_plug_thing = Thing.get_item(
                THING_UID_TREE_IN_CORRIDOR_PLUG
            )
            self.treeincorridor_plug_thing.listen_event(
                self.thing_status_changed, EventFilter(ThingStatusInfoChangedEvent)
            )
            logger.info("Thing   = %s", self.treeincorridor_plug_thing.label)
            logger.info("Status  = %s", self.treeincorridor_plug_thing.status)
        except ItemNotFoundException:
            logger.warning("Thing %s does not exist", DEVICE_NAME_OUTDOOR_PLUG_STATE)
            self.treeincorridor_plug_thing = None

    def set_lights(self, change_state_request=True, switch_all=True, state="ON"):
        """set the state of the christmaslight"""
        logger.info("set christmaslight: %s", state)
        if change_state_request:
            self.christmaslights_state = False
        self.openhab.send_command(DEVICE_NAME_OUTDOOR_PLUG_STATE, state)
        if switch_all:
            self.openhab.send_command(DEVICE_NAME_CANDLE_ARCH_PLUG_STATE, state)
            self.openhab.send_command(DEVICE_NAME_TREE_IN_CORRIDOR_PLUG_STATE, state)

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

        logger.info(
            "rule fired because of %s %s --> %s",
            event.name,
            event.old_status,
            event.status,
        )

        if self.is_dark_outside(
            self.is_dark_outside(self.dark_outside_item.get_value())
        ):
            if str(event.value) == "ON":
                self.set_lights(
                    change_state_request=False, switch_all=False, state="ON"
                )
            else:
                if not self.christmaslights_state:
                    self.set_lights(
                        change_state_request=False, switch_all=False, state="OFF"
                    )

    def sun_state_changed(self, event):
        """checks if it is dark outside"""
        assert isinstance(event, ItemStateUpdatedEvent)

        logger.info(
            "rule fired because of %s %s --> %s",
            event.name,
            event.old_status,
            event.status,
        )
        self.timer_expired()


# Rules
ChristmasLights()
