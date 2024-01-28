"""handle all zigbee items of LIVARNO (LIDL)"""

import logging  # required for extended logging

import HABApp
from HABApp.core.events import (
    ValueUpdateEvent,
    ValueUpdateEventFilter,
)
from HABApp.core.types import HSB
from HABApp.openhab.events import ItemStateUpdatedEvent, ItemStateUpdatedEventFilter
from HABApp.openhab.items import (
    SwitchItem,
    NumberItem,
    DimmerItem,
    StringItem,
    ColorItem,
)

COLOR_TEMP_OFFSET = 153
COLOR_TEMP_SCALE = 3.47
OUTDOOR_SPOTLIGHT_NAME_PREFIX = "Strahler"
OUTDOOR_PLUG_NAME_PREFIX = "Steckdose"

logger = logging.getLogger("Livarno")
logger.setLevel(logging.DEBUG)


class LivarnoZigbeeDevices(HABApp.Rule):
    """handle any zigbee device of IKEA"""

    def __init__(self):
        """initialize and create all elements for items defined in parameter file"""

        super().__init__()

        logger.info("Start")
        param_file = "livarno_param_file"
        # read the outdoor spotlights from the parameter file
        self.outdoor_spotlights = HABApp.DictParameter(
            param_file, "OutdoorSpotlight", default_value=None
        )
        # read the outdoor plugs from the parameter file
        self.outdoor_plugs = HABApp.DictParameter(
            param_file, "OutdoorPlug", default_value=None
        )

        # map to convert MQTT states to switch states
        self.state_map = {"False": "OFF", "True": "ON", "false": "OFF", "true": "ON"}
        # hold the base path for the MQTT topic
        self.mqtt_base_topic = "zigbee2mqtt/Livarno/"

        for outdoor_spotlight in self.outdoor_spotlights.values():
            mqtt_outdoor_spotlight_topic = (
                self.mqtt_base_topic + "AussenStrahler/" + outdoor_spotlight
            )
            self.listen_event(
                mqtt_outdoor_spotlight_topic,
                self.mqtt_outdoor_spotlight_updated,
                ValueUpdateEventFilter(),
            )
            logger.info("added listener for %s", mqtt_outdoor_spotlight_topic)
        logger.info(" -- mqtt listener for spotlights done")

        for outdoor_plug in self.outdoor_plugs.values():
            mqtt_outdoor_plug_topic = (
                self.mqtt_base_topic + "AussenSteckdose/" + outdoor_plug
            )
            self.listen_event(
                mqtt_outdoor_plug_topic,
                self.outdoor_plug_updated,
                ValueUpdateEventFilter(),
            )
            logger.info("added listener for %s", mqtt_outdoor_plug_topic)
        logger.info(" -- mqtt listener for plus done")

        validator = {
            "OutdoorSpotlight": {str: str},
            "OutdoorPlug": {str: str},
        }
        HABApp.parameters.set_file_validator(param_file, validator)

        self.init_outdoor_spotlight()
        self.init_outdoor_plug()

        logger.info("rule LivarnoZigbeeDevices started")

    # helpers
    #########
    def oh_switch_item_changed(self, oh_switch_item, new_value):
        """helper function to check if a dimmer item has changed"""

        ret = False
        state = oh_switch_item.get_value("OFF")
        if (state == "None") or (state is None):
            ret = True
        else:
            if (state == "ON" and new_value == "OFF") or (
                state == "OFF" and new_value == "ON"
            ):
                ret = True
        logger.debug(
            "%s: for %s %s <-- %s vs. %s",
            self.oh_switch_item_changed.__name__,
            oh_switch_item.name,
            ret,
            state,
            new_value,
        )
        return ret

    def oh_dimmer_item_changed(self, oh_dimmer_item, new_value):
        """helper function to check if a dimmer item has changed"""

        ret = False
        value = int(oh_dimmer_item.get_value(0))
        if value == "None":
            ret = True
        else:
            if abs(value - new_value) > 5:
                ret = True
        logger.debug(
            "%s: for %s %s <-- %s vs. %s",
            self.oh_dimmer_item_changed.__name__,
            oh_dimmer_item.name,
            ret,
            value,
            new_value,
        )
        return ret

    def oh_color_item_changed(self, oh_color_item, new_value_x, new_value_y):
        """helper function to check if a color item has changed"""

        logger.info("Cannot convert from CIE 1931 color space to RGB")
        return

        ret = False
        value = oh_color_item.get_rgb()
        if value == "None":
            ret = True
        else:
            if abs(value - new_value) > 5:
                ret = True
        logger.debug(
            "%s: for %s %s <-- %s vs. %s",
            self.oh_dimmer_item_changed.__name__,
            oh_dimmer_item.name,
            ret,
            value,
            new_value,
        )
        return ret

    def oh_number_item_changed(self, oh_number_item, new_value):
        """helper function to check if a number item has changed"""

        ret = False
        value = int(oh_number_item.get_value(0))
        if value == "None":
            ret = True
        else:
            if value != new_value:
                ret = True
        logger.debug(
            "%s: for %s %s <-- %s vs. %s",
            self.oh_number_item_changed.__name__,
            oh_number_item.name,
            ret,
            value,
            new_value,
        )
        return ret

    def extract_mqtt_item_name(self, oh_item_name):
        """helper function to extract the mqtt item name from the OH topic"""

        logger.debug("%s: for %s", self.extract_mqtt_item_name.__name__, oh_item_name)

        _oh_item_name = oh_item_name.rsplit("_", 1)[0]
        logger.debug("splitting -> %s", _oh_item_name)
        _oh_item_name = _oh_item_name.replace("_Dimmer", "").replace("_ColorTemp", "")
        logger.debug("replacing -> %s", _oh_item_name)
        _oh_item_name = _oh_item_name.replace(OUTDOOR_SPOTLIGHT_NAME_PREFIX, "")
        _oh_item_name = _oh_item_name.replace(OUTDOOR_PLUG_NAME_PREFIX, "")
        logger.debug("replacing and returning -> %s", _oh_item_name)
        return _oh_item_name

    def extract_oh_item_name(self, mqtt_topic):
        """helper function to extract the OH name from the MQTT topic"""

        logger.debug("%s: from %s", self.extract_oh_item_name.__name__, mqtt_topic)

        _mqtt_topic = mqtt_topic.split("/")[3]
        logger.debug("extracted %s", _mqtt_topic)
        return _mqtt_topic

    def oh_switch_item_update(self, event):
        """callback function for changes in switch items"""

        assert isinstance(event, ItemStateUpdatedEvent)
        logger.debug(
            "%s: received %s <- %s",
            self.oh_switch_item_update.__name__,
            event.name,
            event.value,
        )
        if OUTDOOR_PLUG_NAME_PREFIX in event.name:
            mqtt_topic = (
                self.mqtt_base_topic
                + "AussenSteckdose/"
                + self.extract_mqtt_item_name(event.name)
                + "/set"
            )
        else:
            mqtt_topic = (
                self.mqtt_base_topic
                + "AussenStrahler/"
                + self.extract_mqtt_item_name(event.name)
                + "/set"
            )
        mqtt_topic_value = '{ "state": "' + str(event.value) + '"}'
        logger.info("send - %s: %s", mqtt_topic, mqtt_topic_value)
        self.mqtt.publish(mqtt_topic, mqtt_topic_value)

    def oh_dimmer_item_update(self, event):
        """callback function for changes in dimmer items"""

        assert isinstance(event, ItemStateUpdatedEvent)
        logger.debug(
            "%s: received %s <- %s",
            self.oh_dimmer_item_update.__name__,
            event.name,
            event.value,
        )

        mqtt_name = self.extract_mqtt_item_name(event.name)
        transition_item_value = 0

        mqtt_topic = self.mqtt_base_topic + "AussenStrahler/" + mqtt_name + "/set"
        # value conversion see https://www.zigbee2mqtt.io/devices/LED1732G11.html#light
        mqtt_value = int(event.value)
        if "_Dimmer" in event.name:
            mqtt_topic_value = '{ "brightness": '
            mqtt_value = int(mqtt_value)
        elif "_ColorTemp" in event.name:
            mqtt_topic_value = '{ "color_temp": '
            mqtt_value = int(mqtt_value * COLOR_TEMP_SCALE) + COLOR_TEMP_OFFSET
        else:
            logger.error(
                "wrong callback %s for %s",
                self.oh_dimmer_item_update.__name__,
                event.name,
            )
            return

        mqtt_topic_value = mqtt_topic_value + str(mqtt_value)

        if self.openhab.item_exists(
            OUTDOOR_SPOTLIGHT_NAME_PREFIX + mqtt_name + "_Transition"
        ):
            transition_item_value = NumberItem.get_item(
                OUTDOOR_SPOTLIGHT_NAME_PREFIX + mqtt_name + "_Transition"
            ).get_value(5)

        if transition_item_value != 0:
            mqtt_topic_value = (
                mqtt_topic_value + ', "transition": ' + str(int(transition_item_value))
            )

        mqtt_topic_value = mqtt_topic_value + "}"
        logger.info("send - %s: %s", mqtt_topic, mqtt_topic_value)
        self.mqtt.publish(mqtt_topic, mqtt_topic_value)

    def oh_color_item_update(self, event):
        """callback function for changes in color items"""

        assert isinstance(event, ItemStateUpdatedEvent)
        logger.debug(
            "%s: received %s <- %s",
            self.oh_color_item_update.__name__,
            event.name,
            event.value,
        )

        mqtt_name = self.extract_mqtt_item_name(event.name)

        HSB_value = event.value
        mqtt_topic = self.mqtt_base_topic + "AussenStrahler/" + mqtt_name + "/set"
        # value conversion see https://www.zigbee2mqtt.io/devices/LED1732G11.html#light
        if "_Color" in event.name:
            mqtt_topic_value = '{ "color": {'
            hsb_color = HSB(HSB_value[0], HSB_value[1], HSB_value[2])
            rgb_color = hsb_color.to_rgb()
            logger.debug("RGB=%s", rgb_color)
            mqtt_topic_value = mqtt_topic_value + '"r": ' + str(rgb_color.red) + ", "
            mqtt_topic_value = mqtt_topic_value + '"g": ' + str(rgb_color.green) + ", "
            mqtt_topic_value = mqtt_topic_value + '"b": ' + str(rgb_color.blue) + "} "
        else:
            logger.error(
                "wrong callback %s for %s",
                self.oh_color_item_update.__name__,
                event.name,
            )
            return

        mqtt_topic_value = mqtt_topic_value + "}"
        logger.info("send - %s: %s", mqtt_topic, mqtt_topic_value)
        self.mqtt.publish(mqtt_topic, mqtt_topic_value)

    def oh_number_item_update(self, event):
        """callback function for changes in number items"""

        assert isinstance(event, ItemStateUpdatedEvent)
        logger.debug(
            "%s: received %s <- %s",
            self.oh_number_item_update.__name__,
            event.name,
            event.value,
        )

        mqtt_name = self.extract_mqtt_item_name(event.name)

        mqtt_topic = self.mqtt_base_topic + "AussenStrahler/" + mqtt_name + "/set"
        value = int(event.value)
        if "_Dimmer" in event.name:
            mqtt_topic_value = '{ "brightness'
        else:
            if "_ColorTemp" in event.name:
                mqtt_topic_value = '{ "color_temp'
                value = int(value * COLOR_TEMP_SCALE)
            else:
                logger.error(
                    "wrong callback %s for %s",
                    self.oh_number_item_update.__name__,
                    event.name,
                )
                return

        if "_Step" in event.name:
            mqtt_topic_value = mqtt_topic_value + "_step"
        else:
            if "_Move" in event.name:
                mqtt_topic_value = mqtt_topic_value + "_move"
            else:
                logger.error(
                    "wrong callback %s for %s",
                    self.oh_number_item_update.__name__,
                    event.name,
                )
                return

        mqtt_topic_value = mqtt_topic_value + '": ' + str(value) + "}"
        logger.info("send - %s: %s", mqtt_topic, mqtt_topic_value)
        self.mqtt.publish(mqtt_topic, mqtt_topic_value)

    def oh_string_item_update(self, event):
        """callback function for changes in string items"""

        assert isinstance(event, ItemStateUpdatedEvent)
        logger.debug(
            "%s: received %s <- %s",
            self.oh_string_item_update.__name__,
            event.name,
            event.value,
        )

        mqtt_name = self.extract_mqtt_item_name(event.name)

        mqtt_topic = self.mqtt_base_topic + "AussenStrahler/" + mqtt_name + "/set"
        if "_ColorTemp_String" in event.name:
            mqtt_topic_value = '{ "color_temp'
        else:
            if "_Effect" in event.name:
                mqtt_topic_value = '{ "effect'
            else:
                logger.error(
                    "wrong callback %s for %s",
                    self.oh_string_item_update.__name__,
                    event.name,
                )
                return

        mqtt_topic_value = mqtt_topic_value + '": "' + str(event.value) + '"}'

        logger.info("send - %s: %s", mqtt_topic, mqtt_topic_value)
        self.mqtt.publish(mqtt_topic, mqtt_topic_value)

    ###############################################################################
    # Ambient Color Lights
    ###############################################################################

    def init_outdoor_spotlight(self):
        """ "initialize the light elements

        register to OpenHAB items
        register to MQTT topics
        see https://www.zigbee2mqtt.io/devices/HG08010.html"""

        for outdoor_spotlight in self.outdoor_spotlights.values():
            light_equipment_name = OUTDOOR_SPOTLIGHT_NAME_PREFIX + outdoor_spotlight
            state_item_name = light_equipment_name + "_State"
            if self.openhab.item_exists(state_item_name):
                switch_item_light = SwitchItem.get_item(state_item_name)
                switch_item_light.listen_event(
                    self.oh_switch_item_update, ItemStateUpdatedEventFilter()
                )
                logger.debug("Added listener for %s", state_item_name)
            else:
                logger.error("%s does not exist", state_item_name)

            dimmer_item_name = light_equipment_name + "_Dimmer"
            if self.openhab.item_exists(dimmer_item_name):
                dimmer_item_light = DimmerItem.get_item(dimmer_item_name)
                dimmer_item_light.listen_event(
                    self.oh_dimmer_item_update, ItemStateUpdatedEventFilter()
                )
                logger.debug("Added listener for %s", dimmer_item_name)
            else:
                logger.error("%s does not exist", dimmer_item_name)

            dimmer_move_item_name = light_equipment_name + "_Dimmer_Move"
            if self.openhab.item_exists(dimmer_move_item_name):
                dimmer_move_item_light = NumberItem.get_item(dimmer_move_item_name)
                dimmer_move_item_light.listen_event(
                    self.oh_number_item_update, ItemStateUpdatedEventFilter()
                )
                logger.debug("Added listener for %s", dimmer_move_item_name)
            else:
                logger.error("%s does not exist", dimmer_move_item_name)

            dimmer_step_item_name = light_equipment_name + "_Dimmer_Step"
            if self.openhab.item_exists(dimmer_step_item_name):
                dimmer_step_item_light = NumberItem.get_item(dimmer_step_item_name)
                dimmer_step_item_light.listen_event(
                    self.oh_number_item_update, ItemStateUpdatedEventFilter()
                )
                logger.debug("Added listener for %s", dimmer_step_item_name)
            else:
                logger.error("%s does not exist", dimmer_step_item_name)

            color_item_name = light_equipment_name + "_Color"
            if self.openhab.item_exists(color_item_name):
                color_item_light = ColorItem.get_item(color_item_name)
                color_item_light = color_item_light.get_item(color_item_name)
                color_item_light.listen_event(
                    self.oh_color_item_update, ItemStateUpdatedEventFilter()
                )
                logger.debug("Added listener for %s", color_item_name)
            else:
                logger.error("%s does not exist", color_item_name)

            color_temp_string_item_name = light_equipment_name + "_Color_String"
            if self.openhab.item_exists(color_temp_string_item_name):
                color_temp_string_item = StringItem.get_item(
                    color_temp_string_item_name
                )
                color_temp_string_item.listen_event(
                    self.oh_string_item_update, ItemStateUpdatedEventFilter()
                )
                logger.debug("Added listener for %s", color_temp_string_item_name)
            else:
                logger.error("%s does not exist", color_temp_string_item_name)

            color_temp_move_item_name = light_equipment_name + "_ColorTemp_Move"
            if self.openhab.item_exists(color_temp_move_item_name):
                color_temp_move_item = NumberItem.get_item(color_temp_move_item_name)
                color_temp_move_item.listen_event(
                    self.oh_number_item_update, ItemStateUpdatedEventFilter()
                )
                logger.debug("Added listener for %s", color_temp_move_item_name)
            else:
                logger.error("%s does not exist", color_temp_move_item_name)

            color_temp_step_item_name = light_equipment_name + "_ColorTemp_Step"
            if self.openhab.item_exists(color_temp_step_item_name):
                color_temp_step_item = NumberItem.get_item(color_temp_step_item_name)
                color_temp_step_item.listen_event(
                    self.oh_number_item_update, ItemStateUpdatedEventFilter()
                )
                logger.debug("Added listener for %s", color_temp_step_item_name)
            else:
                logger.error("%s does not exist", color_temp_step_item_name)

            effect_item_name = light_equipment_name + "_Effect"
            if self.openhab.item_exists(effect_item_name):
                effect_item = StringItem.get_item(effect_item_name)
                effect_item.listen_event(
                    self.oh_string_item_update, ItemStateUpdatedEventFilter()
                )
                logger.debug("Added listener for %s", effect_item_name)
            else:
                logger.error("%s does not exist", effect_item_name)

            transition_item_name = light_equipment_name + "_Transition"
            if self.openhab.item_exists(transition_item_name):
                transition_item = NumberItem.get_item(transition_item_name)
                transition_item.listen_event(
                    self.oh_number_item_update, ItemStateUpdatedEventFilter()
                )
                logger.debug("Added listener for %s", transition_item_name)
            else:
                logger.error("%s does not exist", transition_item_name)

        logger.info("OH - spotlights are setup")

    def mqtt_outdoor_spotlight_updated(self, event: ValueUpdateEvent):
        """handle changes in the mqtt topic of outdoor_spotlight elements"""

        assert isinstance(event, ValueUpdateEvent), type(event)
        logger.info(
            "%s: mqtt topic %s updated to %s",
            self.mqtt_outdoor_spotlight_updated.__name__,
            event.name,
            str(event.value),
        )

        if "state" in event.value:
            state_item_name = (
                OUTDOOR_SPOTLIGHT_NAME_PREFIX
                + self.extract_oh_item_name(event.name)
                + "_State"
            )
            if self.openhab.item_exists(state_item_name):
                switch_item_state = SwitchItem.get_item(state_item_name)
                new_value = str(event.value["state"])
                if self.oh_switch_item_changed(switch_item_state, new_value):
                    switch_item_state.oh_send_command(new_value)
                logger.info("state     : %s", new_value)
            else:
                logger.error("item %s does not exist", state_item_name)

        if "brightness" in event.value:
            dimmer_item_name = (
                OUTDOOR_SPOTLIGHT_NAME_PREFIX
                + self.extract_oh_item_name(event.name)
                + "_Dimmer"
            )
            if self.openhab.item_exists(dimmer_item_name):
                dimmer_item_bright = DimmerItem.get_item(dimmer_item_name)
                new_value = int(event.value["brightness"])
                if self.oh_dimmer_item_changed(dimmer_item_bright, new_value):
                    # Livarno https://www.zigbee2mqtt.io/devices/HG08010.html#light
                    # 0 ... 254
                    dimmer_item_bright.oh_send_command(new_value)
                logger.info("brightness: %s", str(new_value))
            else:
                logger.error("item %s does not exist", dimmer_item_name)

        if "color" in event.value and "color_" not in event.value:
            color_item_name = (
                OUTDOOR_SPOTLIGHT_NAME_PREFIX
                + self.extract_oh_item_name(event.name)
                + "_Color"
            )
            if self.openhab.item_exists(color_item_name):
                color_item = ColorItem.get_item(color_item_name)
                new_value_x = event.value["color"]["x"]
                new_value_y = event.value["color"]["y"]
                if self.oh_color_item_changed(
                    color_item, new_value_x=new_value_x, new_value_y=new_value_y
                ):
                    color_item.oh_send_command(new_value)
                logger.info("color: x:%s y:%s", str(new_value_x), str(new_value_y))
            else:
                logger.error("item %s does not exist", color_item_name)

        if "color_temp" in event.value:
            color_temp_item_name = (
                OUTDOOR_SPOTLIGHT_NAME_PREFIX
                + self.extract_oh_item_name(event.name)
                + "_ColorTemp"
            )
            if self.openhab.item_exists(color_temp_item_name):
                color_temp_item = DimmerItem.get_item(color_temp_item_name)
                new_value = int(
                    (int(event.value["color_temp"]) - COLOR_TEMP_OFFSET)
                    / COLOR_TEMP_SCALE
                )
                if self.oh_dimmer_item_changed(color_temp_item, new_value):
                    # LIVARNO https://www.zigbee2mqtt.io/devices/HG08010.html#light
                    # 153 ... 500
                    color_temp_item.oh_send_command(new_value)
                logger.info("color_temp : %s", str(new_value))
            else:
                logger.error("item %s does not exist", color_temp_item_name)

        if "update" in event.value:
            if "state" in event.value["update"]:
                update_item_name = (
                    OUTDOOR_SPOTLIGHT_NAME_PREFIX
                    + self.extract_oh_item_name(event.name)
                    + "_UpdatePending"
                )
                if self.openhab.item_exists(update_item_name):
                    update_item = SwitchItem.get_item(update_item_name)
                    new_value = str(event.value["update"]["state"])
                    if new_value == "available":
                        new_value = "ON"
                    else:
                        new_value = "OFF"
                    if self.oh_switch_item_changed(update_item, new_value):
                        update_item.oh_send_command(new_value)
                    logger.info("update    : %s", new_value)
                else:
                    logger.error("item %s does not exist", update_item_name)

    ###############################################################################
    # Outdoor plugs
    ###############################################################################

    def init_outdoor_plug(self):
        """ "initialize the plug elements

        register to OpenHAB items
        register to MQTT topics
        see https://www.zigbee2mqtt.io/devices/HG06620.html"""

        for outdoor_plug in self.outdoor_plugs.values():
            outdoor_plug_equipment_name = OUTDOOR_PLUG_NAME_PREFIX + outdoor_plug
            state_item_name = outdoor_plug_equipment_name + "_State"
            if self.openhab.item_exists(state_item_name):
                switch_item_light = SwitchItem.get_item(state_item_name)
                switch_item_light.listen_event(
                    self.oh_switch_item_update, ItemStateUpdatedEventFilter()
                )
                logger.debug("Added listener for %s", state_item_name)
            else:
                logger.error("%s does not exist", state_item_name)

        logger.info("OH - plugs are setup")

    def outdoor_plug_updated(self, event):
        """handle changes in MQTT topic for outdoor plugs"""

        assert isinstance(event, ValueUpdateEvent), type(event)
        logger.info(
            "%s: mqtt topic %s updated to %s",
            self.outdoor_plug_updated.__name__,
            event.name,
            str(event.value),
        )

        if "state" in event.value:
            state_item_name = (
                OUTDOOR_PLUG_NAME_PREFIX
                + self.extract_oh_item_name(event.name)
                + "_State"
            )
            if self.openhab.item_exists(state_item_name):
                switch_item_state = SwitchItem.get_item(state_item_name)
                new_value = str(event.value["state"])
                if self.oh_switch_item_changed(switch_item_state, new_value):
                    switch_item_state.oh_send_command(new_value)
                logger.info("state     : %s", new_value)
            else:
                logger.error("item %s does not exist", state_item_name)

        link_quality = 100
        if "linkquality" in event.value:
            link_quality = event.value["linkquality"]

        update_available = False
        if "update" in event.value:
            if "available" == event.value["update"]["state"]:
                update_available = True

        topic_items = str(event.name).split("/")

        logger.info("Item       : %s", topic_items[2] + topic_items[3])
        logger.info("LinkQuality: %s", str(link_quality))
        logger.info("FW Update  : %s", str(update_available))

        exitcode = 0
        update_pending = topic_items[2] + topic_items[3] + "_UpdatePending"
        if self.openhab.item_exists(update_pending):
            my_oh_item_updatepending = SwitchItem.get_item(update_pending)
        else:
            logger.error("item %s does not exist", update_pending)
            exitcode = 3

        if exitcode != 0:
            return exitcode
        if self.oh_switch_item_changed(
            my_oh_item_updatepending, self.state_map[str(update_available)]
        ):
            my_oh_item_updatepending.oh_send_command(
                self.state_map[str(update_available)]
            )


LivarnoZigbeeDevices()
