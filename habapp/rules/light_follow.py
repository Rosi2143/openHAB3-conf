"""makes other light(s) follow a leading light"""

import logging  # required for extended logging

import HABApp
from HABApp.openhab.items import NumberItem, GroupItem, ContactItem
from HABApp.core.events import ValueChangeEventFilter

logger = logging.getLogger("Light")


class Light(HABApp.Rule):
    """This class handles Hue internal states."""

    def __init__(self):
        """initialize the logger test"""
        super().__init__()

        param_file = "light"
        # read the outdoor spotlights from the parameter file
        self.lights_follow = HABApp.DictParameter(param_file, "lights")

        oh_group_main_lights = GroupItem.get_item("gHauptLichter")
        for oh_item in oh_group_main_lights.members:
            oh_item.listen_event(self.light_following, ValueChangeEventFilter())

        oh_item_front_door = ContactItem.get_item("TuerHaustuer_StateContact")
        oh_item_front_door.listen_event(
            self.following_frontdoor, ValueChangeEventFilter(value="OPEN")
        )

        oh_item_upper_storage = ContactItem.get_item("TuerKammer_OpenState")
        oh_item_upper_storage.listen_event(
            self.following_upper_storage, ValueChangeEventFilter()
        )

    def light_following(self, event):
        """make all office lights follow the main light"""

        logger.info(
            "rule fired because of %s %s --> %s",
            event.name,
            event.old_value,
            event.value,
        )

        if not event.name in self.lights_follow:
            logger.error("element %s not found in %s", event.name, self.lights_follow)
        else:
            light = self.lights_follow[event.name]
            logger.info("setting %s to %s", light, event.value)
            self.openhab.send_command(light, str(event.value))

    def following_frontdoor(self, event):
        """turn frontdoor light ON when door opens"""

        logger.info(
            "rule fired because of %s %s --> %s",
            event.name,
            event.old_value,
            event.value,
        )

        outside_light = NumberItem.get_item(
            "BewegungsmelderHaustuer_Illumination"
        ).get_value(0)
        if outside_light < 10:
            self.openhab.send_command("LichtFlurErdgeschoss_State", "ON")
            self.openhab.send_command("LichtHaustuer_State", "ON")
            logger.info("turned lights ON")
        else:
            logger.info(
                "not dark enough outside (%d>=10)",
                outside_light,
            )

    def following_upper_storage(self, event):
        """make all office lights follow the main light"""

        logger.info(
            "rule fired because of %s %s --> %s",
            event.name,
            event.old_value,
            event.value,
        )

        if str(event.value) == "OPEN":
            self.openhab.send_command("LichtKammer_State", "ON")
        else:
            self.openhab.send_command("LichtKammer_State", "OFF")


Light()
