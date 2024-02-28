"""This script handles HABPanel notification items."""

import logging  # required for extended logging

import HABApp
from HABApp.openhab.items import ContactItem, GroupItem
from HABApp.core.events import ValueChangeEventFilter

logger = logging.getLogger("Notification")


class Notifications(HABApp.Rule):
    """This class handles Hue internal states."""

    def __init__(self):
        """initialize the logger test"""
        super().__init__()

        oh_item_light_upper_floor = GroupItem.get_item("gLichterObergeschoss")
        oh_item_light_upper_floor.listen_event(
            self.first_floor_lights, ValueChangeEventFilter()
        )

        oh_item_light_upper_floor = GroupItem.get_item("gLichterErdgeschoss")
        oh_item_light_upper_floor.listen_event(
            self.ground_floor_lights, ValueChangeEventFilter()
        )

        oh_item_light_upper_floor = GroupItem.get_item("gLichterKeller")
        oh_item_light_upper_floor.listen_event(
            self.basement_lights, ValueChangeEventFilter()
        )

        oh_item_light_upper_floor = GroupItem.get_item("gAussenTueren")
        oh_item_light_upper_floor.listen_event(
            self.security_state, ValueChangeEventFilter()
        )
        oh_item_light_upper_floor = GroupItem.get_item("gFenster")
        oh_item_light_upper_floor.listen_event(
            self.security_state, ValueChangeEventFilter()
        )
        oh_item_light_upper_floor = ContactItem.get_item("TuerWaschkueche_OpenState")
        oh_item_light_upper_floor.listen_event(
            self.security_state, ValueChangeEventFilter()
        )

        oh_item_light_upper_floor = GroupItem.get_item("gThingItems")
        oh_item_light_upper_floor.listen_event(
            self.thing_state, ValueChangeEventFilter()
        )

        logger.info("Notification rule initialized")

    def first_floor_lights(self, event):
        """
        notification for first floor lights

        Args:
            event (_type_): triggering event
        """
        logger.info(
            "rule fired because of %s %s --> %s",
            event.name,
            event.old_value,
            event.value,
        )

        self.openhab.post_update("LightNotification_FF", str(event.value))

    def ground_floor_lights(self, event):
        """
        notification for ground floor lights

        Args:
            event (_type_): triggering event
        """
        logger.info(
            "rule fired because of %s %s --> %s",
            event.name,
            event.old_value,
            event.value,
        )

        self.openhab.post_update("LightNotification_GF", str(event.value))

    def basement_lights(self, event):
        """
        notification for basement lights

        Args:
            event (_type_): triggering event
        """
        logger.info(
            "rule fired because of %s %s --> %s",
            event.name,
            event.old_value,
            event.value,
        )

        self.openhab.post_update("LightNotification_BM", str(event.value))

    def security_state(self, event):
        """
        notification for security state

        Args:
            event (_type_): triggering event
        """
        logger.info(
            "rule fired because of %s %s --> %s",
            event.name,
            event.old_value,
            event.value,
        )

        if (
            (GroupItem.get_item("gAussenTueren").get_value() != "OPEN")
            and (GroupItem.get_item("gFenster").get_value() != "OPEN")
            and (
                ContactItem.get_item("TuerWaschkueche_OpenState").get_value() != "OPEN"
            )
        ):
            self.openhab.send_command("SomeExternalWindowsDoorsOpen", "OFF")
        else:
            self.openhab.send_command("SomeExternalWindowsDoorsOpen", "ON")

    def thing_state(self, event):
        """
        notification for security state

        Args:
            event (_type_): triggering event
        """
        logger.info(
            "rule fired because of %s %s --> %s",
            event.name,
            event.old_value,
            event.value,
        )

        if GroupItem.get_item("gThingItems").get_value() != "OFF":
            self.openhab.send_command("ThingItems", "ON")
        else:
            self.openhab.send_command("ThingItems", "OFF")


Notifications()
