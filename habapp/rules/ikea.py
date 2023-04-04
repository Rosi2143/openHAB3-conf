"""handle all zigbee items of IKEA"""

import logging  # required for extended logging

import json

import HABApp
from HABApp.core.events import ValueUpdateEvent, ValueUpdateEventFilter
from HABApp.openhab.events import ItemStateEvent, ItemStateEventFilter
from HABApp.openhab.items import SwitchItem, NumberItem, DimmerItem, StringItem

logger = logging.getLogger('Ikea')


class IkeaZigbeeDevices(HABApp.Rule):
    """handle any zigbee device of IKEA"""

    def __init__(self):
        """initialize and create all elements for items defined in parameter file"""

        super().__init__()

        parm_file = 'ikea_param_file'
        # read the low bat threshold from the parameter file
        self.min_battery_charge = HABApp.Parameter(
            parm_file, 'min_battery_charge', default_value=20)
        # read the motion detectors from the parameter file
        self.motion_detectors = HABApp.DictParameter(
            parm_file, 'MotionDetectors', default_value=None)
        # read the lights from the parameter file
        self.lights = HABApp.DictParameter(
            parm_file, 'Lights', default_value=None)
        # read the remote controls from the parameter file
        self.remote_controls = HABApp.DictParameter(
            parm_file, 'RemoteControls', default_value=None)

        # map to convert MQTT states to switch states
        self.state_map = {'False': 'OFF',
                          'True': 'ON',
                          'false': 'OFF',
                          'true': 'ON'
                          }
        # hold the base path for the MQTT topic
        self.mqtt_base_topic = "zigbee2mqtt/IKEA/"

        for motion_detector in self.motion_detectors.values():
            mqtt_motion_detector_topic = self.mqtt_base_topic + \
                'Bewegungsmelder/' + motion_detector
            self.listen_event(mqtt_motion_detector_topic,
                              self.motion_detect_updated, ValueUpdateEventFilter())
            logger.info("added listener for %s", mqtt_motion_detector_topic)

        for remote_control in self.remote_controls.values():
            mqtt_remote_control_topic = self.mqtt_base_topic + \
                'Fernbedienung/' + remote_control
            self.listen_event(mqtt_remote_control_topic,
                              self.remote_control_updated, ValueUpdateEventFilter())
            logger.info("added listener for %s", mqtt_remote_control_topic)

        validator = {
            'min_battery_charge': int,
            'MotionDetectors': {str: str},
            'RemoteControls': {str: str},
            'Lights': {str: str}
        }
        HABApp.parameters.set_file_validator(parm_file, validator)

        self.init_light()

        logger.info('rule IkeaZigbeeDevices started')

# helpers
#########
    def oh_switch_item_changed(self, oh_switch_item, new_value):
        """helper function to check if a dimmer item has changed"""

        ret = False
        state = oh_switch_item.get_value("OFF")
        if (state == "None") or (state is None):
            ret = True
        else:
            if ((state == "ON" and new_value == "OFF") or (state == "OFF" and new_value == "ON")):
                ret = True
        logger.debug(
            "OH_switch_item_Changed for %s %s <-- {oh_switch_item.get_value()} vs. %s",
            oh_switch_item.name, ret, new_value)
        return ret

    def oh_dimmer_item_changed(self, oh_dimmer_item, new_value):
        """helper function to check if a dimmer item has changed"""

        ret = False
        # consider conversion of dimmer to IKEA / *2.04
        value = int(oh_dimmer_item.get_value(0))
        if value == "None":
            ret = True
        else:
            if abs(value - new_value) > 5:
                ret = True
        logger.debug(
            "OH_dimmer_item_Changed for %s %s <-- %s vs. %s",
            oh_dimmer_item.name, ret, value, new_value)
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
            "OH_NumberItem_Changed for %s %s <-- %s vs. %s",
            oh_number_item.name, ret, value, new_value)
        return ret

    def extract_mqtt_item_name(self, oh_item_name):
        """helper function to extract the mqtt item name from the OH topic"""

        logger.debug(oh_item_name)
        _oh_item_name = oh_item_name.rsplit("_", 1)[0]
        logger.debug(_oh_item_name)
        _oh_item_name = _oh_item_name.replace(
            "_Dimmer", "").replace("_ColorTemp", "")
        logger.debug(_oh_item_name)
        _oh_item_name = _oh_item_name.replace("eLicht", "")
        logger.debug(_oh_item_name)
        return _oh_item_name

    def extract_oh_item_name(self, mqtt_topic):
        """helper function to extract the OH name from the MQTT topic"""

        logger.debug(mqtt_topic)
        _mqtt_topic = mqtt_topic.split("/")[3]
        logger.debug(_mqtt_topic)
        return _mqtt_topic

    def switch_item_update(self, event):
        """callback function for changes in switch items"""

        assert isinstance(event, ItemStateEvent)
        logger.debug("received %s <- %s", event.name, event.value)
        mqtt_topic = self.mqtt_base_topic + "Lampe/" + \
            self.extract_mqtt_item_name(event.name) + "/set"
        mqtt_topic_value = "{ \"state\": \"" + str(event.value) + "\"}"
        logger.info("%s: %s", mqtt_topic, mqtt_topic_value)
        self.mqtt.publish(mqtt_topic, mqtt_topic_value)

    def dimmer_item_update(self, event):
        """callback function for changes in dimmer items"""

        assert isinstance(event, ValueUpdateEvent)
        logger.debug("received %s <- %s", event.name, event.value)

        mqtt_name = self.extract_mqtt_item_name(event.name)
        transition_item_value = 0

        mqtt_topic = self.mqtt_base_topic + "Lampe/" + \
            self.extract_mqtt_item_name(event.name) + "/set"
        # value conversion see https://www.zigbee2mqtt.io/devices/LED1732G11.html#light
        mqtt_value = int(event.value)
        if "_Dimmer" in event.name:
            mqtt_topic_value = "{ \"brightness\": "
            mqtt_value = int(mqtt_value * 2.54)
        else:
            if "_ColorTemp" in event.name:
                mqtt_topic_value = "{ \"color_temp\": "
                mqtt_value = int(mqtt_value * 2.04) + 250
            else:
                logger.error(
                    "wrong callback dimmer_item_update for %s", event.name)
                return

        mqtt_topic_value = mqtt_topic_value + str(mqtt_value)

        if self.openhab.item_exists("Licht" + mqtt_name + "_Transition"):
            transition_item_value = NumberItem.get_item(
                "Licht" + mqtt_name + "_Transition").get_value(5)

        if transition_item_value != 0:
            mqtt_topic_value = mqtt_topic_value + \
                ", \"transition\": " + str(int(transition_item_value))

        mqtt_topic_value = mqtt_topic_value + "}"
        logger.info("%s: %s", mqtt_topic, mqtt_topic_value)
        self.mqtt.publish(mqtt_topic, mqtt_topic_value)

    def numberitem_update(self, event):
        """callback function for changes in number items"""

        assert isinstance(event, ValueUpdateEvent)
        logger.debug("received %s <- %s", event.name, event.value)

        mqtt_name = self.extract_mqtt_item_name(event.name)

        mqtt_topic = self.mqtt_base_topic + "Lampe/" + mqtt_name + "/set"
        value = int(event.value)
        if "_Dimmer" in event.name:
            mqtt_topic_value = "{ \"brightness"
            value = int(value * 2.54)
        else:
            if "_ColorTemp" in event.name:
                mqtt_topic_value = "{ \"color_temp"
                value = int(value * 2.04)
            else:
                logger.error(
                    "wrong callback numberitem_update for %s", event.name)
                return

        if "_Step" in event.name:
            mqtt_topic_value = mqtt_topic_value + "_step"
        else:
            if "_Move" in event.name:
                mqtt_topic_value = mqtt_topic_value + "_move"
            else:
                logger.error(
                    "wrong callback numberitem_update for %s", event.name)
                return

        mqtt_topic_value = mqtt_topic_value + "\": " + str(value) + "}"
        logger.info("%s: %s", mqtt_topic, mqtt_topic_value)
        self.mqtt.publish(mqtt_topic, mqtt_topic_value)

    def stringitem_update(self, event):
        """callback function for changes in string items"""

        assert isinstance(event, ValueUpdateEvent)
        logger.debug("received %s <- %s", event.name, event.value)

        mqtt_name = self.extract_mqtt_item_name(event.name)

        mqtt_topic = self.mqtt_base_topic + "Lampe/" + mqtt_name + "/set"
        if "_ColorTemp_String" in event.name:
            mqtt_topic_value = "{ \"color_temp"
        else:
            if "_Effect" in event.name:
                mqtt_topic_value = "{ \"effect"
            else:
                logger.error(
                    "wrong callback stringitem_update for %s", event.name)
                return

        mqtt_topic_value = mqtt_topic_value + \
            "\": \"" + str(event.value) + "\"}"

        logger.info("%s: %s", mqtt_topic, mqtt_topic_value)
        self.mqtt.publish(mqtt_topic, mqtt_topic_value)

###############################################################################
# Ambient White Lights
###############################################################################

    def init_light(self):
        """"initialize the light elements

        register to OpenHAB items
        register to MQTT topics
        see https://www.zigbee2mqtt.io/devices/LED1545G12.html"""

        for light in self.lights.values():
            light_equipment_name = "eLicht" + light
            state_item_name = light_equipment_name + "_State"
            if self.openhab.item_exists(state_item_name):
                switch_item_light = SwitchItem.get_item(state_item_name)
                switch_item_light.listen_event(
                    self.switch_item_update, ItemStateEventFilter())
            else:
                logger.error("%s does not exist", state_item_name)

            dimmer_item_name = light_equipment_name + "_Dimmer"
            if self.openhab.item_exists(dimmer_item_name):
                dimmer_item_light = DimmerItem.get_item(
                    dimmer_item_name)
                dimmer_item_light.listen_event(
                    self.dimmer_item_update, ItemStateEventFilter())
            else:
                logger.error("%s does not exist", dimmer_item_name)

            dimmer_move_item_name = light_equipment_name + "_Dimmer_Move"
            if self.openhab.item_exists(dimmer_move_item_name):
                dimmer_move_item_light = NumberItem.get_item(
                    dimmer_move_item_name)
                dimmer_move_item_light.listen_event(
                    self.numberitem_update, ItemStateEventFilter())
            else:
                logger.error("%s does not exist", dimmer_move_item_name)

            dimmer_step_item_name = light_equipment_name + "_Dimmer_Step"
            if self.openhab.item_exists(dimmer_step_item_name):
                dimmer_step_item_light = NumberItem.get_item(
                    dimmer_step_item_name)
                dimmer_step_item_light.listen_event(
                    self.numberitem_update, ItemStateEventFilter())
            else:
                logger.error("%s does not exist", dimmer_step_item_name)

            color_temp_item_name = light_equipment_name + "_ColorTemp"
            if self.openhab.item_exists(color_temp_item_name):
                color_temp_item_light = dimmer_item_light.get_item(
                    color_temp_item_name)
                color_temp_item_light.listen_event(
                    self.dimmer_item_update, ItemStateEventFilter())
            else:
                logger.error("%s does not exist", color_temp_item_name)

            color_temp_string_item_name = light_equipment_name + "_ColorTemp_String"
            if self.openhab.item_exists(color_temp_string_item_name):
                color_temp_string_item = StringItem.get_item(
                    color_temp_string_item_name)
                color_temp_string_item.listen_event(
                    self.stringitem_update, ItemStateEventFilter())
            else:
                logger.error("%s does not exist", color_temp_string_item_name)

            color_temp_move_item_name = light_equipment_name + "_ColorTemp_Move"
            if self.openhab.item_exists(color_temp_move_item_name):
                color_temp_move_item = NumberItem.get_item(
                    color_temp_move_item_name)
                color_temp_move_item.listen_event(
                    self.numberitem_update, ItemStateEventFilter())
            else:
                logger.error("%s does not exist", color_temp_move_item_name)

            color_temp_step_item_name = light_equipment_name + "_ColorTemp_Step"
            if self.openhab.item_exists(color_temp_step_item_name):
                color_temp_step_item = NumberItem.get_item(
                    color_temp_step_item_name)
                color_temp_step_item.listen_event(
                    self.numberitem_update, ItemStateEventFilter())
            else:
                logger.error("%s does not exist", color_temp_step_item_name)

            effect_item_name = light_equipment_name + "_Effect"
            if self.openhab.item_exists(effect_item_name):
                effect_item = StringItem.get_item(effect_item_name)
                effect_item.listen_event(
                    self.stringitem_update, ItemStateEventFilter())
            else:
                logger.error("%s does not exist", effect_item_name)

            transition_item_name = light_equipment_name + "_Transition"
            if self.openhab.item_exists(transition_item_name):
                transition_item = NumberItem.get_item(transition_item_name)
                transition_item.listen_event(
                    self.numberitem_update, ItemStateEventFilter())
            else:
                logger.error("%s does not exist", transition_item_name)

            mqtt_light_topic = self.mqtt_base_topic + 'Lampe/' + light
            self.listen_event(mqtt_light_topic,
                              self.light_updated, ValueUpdateEventFilter())
            logger.info("added listener for %s", mqtt_light_topic)

            logger.info("added listener for Light %s", light)
        logger.info('lights are setup')

    def light_updated(self, event):
        """handle changes in the mqtt topic of light elements"""

        assert isinstance(event, ValueUpdateEvent), type(event)
        logger.info("mqtt topic %s updated to %s",
                    event.name, str(event.value))

        if "state" in event.value:
            state_item_name = "Licht" + \
                self.extract_oh_item_name(event.name) + "_State"
            if self.openhab.item_exists(state_item_name):
                switch_item_state = switch_item_state.get_item(state_item_name)
                new_value = str(event.value["state"])
                if self.oh_switch_item_changed(switch_item_state, new_value):
                    switch_item_state.oh_send_command(new_value)
                logger.info("state     : %s", new_value)
            else:
                logger.error("item %s does not exist", state_item_name)

        if "brightness" in event.value:
            dimmer_item_name = "Licht" + \
                self.extract_oh_item_name(event.name) + "_Dimmer"
            if self.openhab.item_exists(dimmer_item_name):
                dimmer_item_bright = dimmer_item_bright.get_item(
                    dimmer_item_name)
                new_value = int(int(event.value["brightness"]) / 2.54)
                if self.oh_dimmer_item_changed(dimmer_item_bright, new_value):
                    # IKEA https://www.zigbee2mqtt.io/devices/LED1732G11.html#light
                    # 0 ... 254
                    dimmer_item_bright.oh_send_command(new_value)
                logger.info("brightness: %s", str(new_value))
            else:
                logger.error("item %s does not exist", dimmer_item_name)

        if "color_temp" in event.value:
            color_temp_item_name = "Licht" + \
                self.extract_oh_item_name(event.name) + "_ColorTemp"
            if self.openhab.item_exists(color_temp_item_name):
                color_temp_item = dimmer_item_bright.get_item(
                    color_temp_item_name)
                new_value = int((int(event.value["color_temp"]) - 250) / 2.04)
                if self.oh_dimmer_item_changed(color_temp_item, new_value):
                    # IKEA https://www.zigbee2mqtt.io/devices/LED1732G11.html#light
                    # 250 ... 454
                    color_temp_item.oh_send_command(new_value)
                logger.info("color_temp : %s", str(new_value))
            else:
                logger.error("item %s does not exist", color_temp_item_name)

        if "update" in event.value:
            if "state" in event.value["update"]:
                update_item_name = "Licht" + \
                    self.extract_oh_item_name(event.name) + "_UpdatePending"
                if self.openhab.item_exists(update_item_name):
                    update_item = switch_item_state.get_item(update_item_name)
                    new_value = str(event.value["update"]["state"])
                    if new_value == "available":
                        new_value = "ON"
                    else:
                        new_value = "OFF"
                    if self.oh_switch_item_changed(update_item, new_value):
                        # IKEA https://www.zigbee2mqtt.io/devices/LED1732G11.html#light
                        # 250 ... 454
                        update_item.oh_send_command(new_value)
                    logger.info("update    : %s", new_value)
                else:
                    logger.error("item %s does not exist", update_item_name)

###############################################################################
# Motion Detector
###############################################################################

    def motion_detect_updated(self, event):
        """handle changes in the MQTT topic for motion detectors."""

        assert isinstance(event, ValueUpdateEvent), type(event)

        battery_charge = 100
        battery_weak = False
        if 'battery' in event.value:
            battery_charge = int(event.value['battery'])
        if battery_charge < self.min_battery_charge:
            battery_weak = True

        occupancy = 'False'
        if 'occupancy' in event.value:
            occupancy = str(event.value['occupancy'])

        link_quality = 100
        if 'linkquality' in event.value:
            link_quality = event.value['linkquality']

        illuminance_above_threshold = False
        if 'illuminance_above_threshold' in event.value:
            illuminance_above_threshold = event.value['illuminance_above_threshold']

        update_available = False
        if 'update' in event.value:
            if "available" == event.value["update"]["state"]:
                update_available = True

        # see naming conventions in ikea.items
        topic_items = str(event.name).split('/')

        logger.debug(
            "mqtt topic %s updated to \n%s", event.name, json.dumps(event.value, indent=2))
        logger.info("Item       : %s", topic_items[2] + topic_items[3])
        logger.info("MotionState: %s", occupancy)
        logger.info("Battery    : %s", str(battery_charge))
        logger.info("BatteryWeak: %s", str(battery_weak))
        logger.info("LinkQuality: %s", str(link_quality))
        logger.info("LightState : %s", str(illuminance_above_threshold))
        logger.info("FW Update  : %s", str(update_available))

        exitcode = 0
        battery_status = topic_items[2] + topic_items[3] + "_BatteryStatus"
        if self.openhab.item_exists(battery_status):
            my_oh_item_batterystate = SwitchItem.get_item(battery_status)
        else:
            logger.error("item %s does not exist", battery_status)
            exitcode = 1

        charging_level = topic_items[2] + topic_items[3] + "_ChargingLevel"
        if self.openhab.item_exists(charging_level):
            my_oh_item_charging_level = NumberItem.get_item(charging_level)
        else:
            logger.error("item %s does not exist", charging_level)
            exitcode = 2

        update_pending = topic_items[2] + topic_items[3] + "_UpdatePending"
        if self.openhab.item_exists(update_pending):
            my_oh_item_updatepending = SwitchItem.get_item(update_pending)
        else:
            logger.error("item %s does not exist", update_pending)
            exitcode = 3

        motion_state = topic_items[2] + topic_items[3] + "_MotionState"
        if self.openhab.item_exists(motion_state):
            my_oh_item_motionstate = SwitchItem.get_item(motion_state)
        else:
            logger.error("item %s does not exist", motion_state)
            exitcode = 4

        motion_detect_state = topic_items[2] + \
            topic_items[3] + "_MotionDetectState"
        if self.openhab.item_exists(motion_detect_state):
            my_oh_item_motiondetectstate = SwitchItem.get_item(
                motion_detect_state)
        else:
            logger.error("item %s does not exist", motion_detect_state)
            exitcode = 5

        if exitcode != 0:
            return exitcode

        my_oh_item_charging_level.oh_send_command(battery_charge)
        my_oh_item_batterystate.oh_send_command(
            self.state_map[str(battery_weak)])
        my_oh_item_updatepending.oh_send_command(
            self.state_map[str(update_available)])
        my_oh_item_motionstate.oh_send_command(self.state_map[str(occupancy)])
        my_oh_item_motiondetectstate.oh_send_command(
            self.state_map[str(illuminance_above_threshold)])

###############################################################################
# Remote Controller
###############################################################################

    def remote_control_updated(self, event):
        """handle changes in MQTT topic for remote control switches"""

        assert isinstance(event, ValueUpdateEvent), type(event)

        battery_charge = 100
        battery_weak = False
        if 'battery' in event.value:
            battery_charge = int(event.value['battery'])
        if battery_charge < self.min_battery_charge:
            battery_weak = True

        action = 'none'
        if 'action' in event.value:
            action = str(event.value['action'])

        link_quality = 100
        if 'linkquality' in event.value:
            link_quality = event.value['linkquality']

        update_available = False
        if 'update' in event.value:
            if "available" == event.value["update"]["state"]:
                update_available = True

        # see naming conventions in ikea.items
        topic_items = str(event.name).split('/')

        logger.debug("mqtt topic %s updated to\n%s", event.name,
                     json.dumps(event.value, indent=2))
        logger.info("Item       : %s", topic_items[2] + topic_items[3])
        logger.info("Action     : %s", action)
        logger.info("Battery    : %s", str(battery_charge))
        logger.info("BatteryWeak: %s", str(battery_weak))
        logger.info("LinkQuality: %s", str(link_quality))
        logger.info("FW Update  : %s", str(update_available))

        exitcode = 0
        battery_status = topic_items[2] + topic_items[3] + "_BatteryStatus"
        if self.openhab.item_exists(battery_status):
            my_oh_item_batterystate = SwitchItem.get_item(battery_status)
        else:
            logger.error("item %s does not exist", battery_status)
            exitcode = 1

        charging_level = topic_items[2] + topic_items[3] + "_ChargingLevel"
        if self.openhab.item_exists(charging_level):
            my_oh_item_charging_level = NumberItem.get_item(charging_level)
        else:
            logger.error("item %s does not exist", charging_level)
            exitcode = 2

        update_pending = topic_items[2] + topic_items[3] + "_UpdatePending"
        if self.openhab.item_exists(update_pending):
            my_oh_item_updatepending = SwitchItem.get_item(update_pending)
        else:
            logger.error("item %s does not exist", update_pending)
            exitcode = 3

        if exitcode != 0:
            return exitcode

        if self.oh_number_item_changed(my_oh_item_charging_level, battery_charge):
            my_oh_item_charging_level.oh_send_command(battery_charge)
        if self.oh_switch_item_changed(my_oh_item_batterystate,
                                       self.state_map[str(battery_weak)]):
            my_oh_item_batterystate.oh_send_command(
                self.state_map[str(battery_weak)])
        if self.oh_switch_item_changed(my_oh_item_updatepending,
                                       self.state_map[str(update_available)]):
            my_oh_item_updatepending.oh_send_command(
                self.state_map[str(update_available)])

        keypress_items = {"toggle": ["_MainButton", "ON"],
                          "brightness_up_click": ["_Up", "ON"],
                          "brightness_down_click": ["_Down", "ON"],
                          "arrow_left_click": ["_Left", "ON"],
                          "arrow_right_click": ["_Right", "ON"],

                          "toggle_hold": ["_MainButton_Long", "ON"],
                          "brightness_up_hold": ["_Up_Long", "ON"],
                          "brightness_down_hold": ["_Down_Long", "ON"],
                          "arrow_left_hold": ["_Left_Long", "ON"],
                          "arrow_right_hold": ["_Right_Long", "ON"],

                          "brightness_up_release": ["_Up_Long", "OFF"],
                          "brightness_down_release": ["_Down_Long", "OFF"],
                          "arrow_left_release": ["_Left_Long", "OFF"],
                          "arrow_right_release": ["_Right_Long", "OFF"],

                          "on": ["_Main", "ON"],
                          "brightness_move_up": ["_MainButton_Long", "ON"],
                          "brightness_stop": ["_MainButton_Long", "OFF"],
                          }

        itemcount = 3
        found_action = False
        for key, item in keypress_items.items():
            logger.debug("check action for %s for %s", action, key)
            key_item_name = topic_items[2] + topic_items[3] + item[0]
            if action == key:
                itemcount = itemcount + 1
                if self.openhab.item_exists(key_item_name):
                    oh_keypress_item = SwitchItem.get_item(key_item_name)
                    logger.debug("found action for %s for %s :: %s --> %s",
                                 action, key, key_item_name, item[1])
                    if self.oh_switch_item_changed(oh_keypress_item, item[1]):
                        oh_keypress_item.oh_send_command(item[1])
                    found_action = True
                    break
                else:
                    logger.error("item %s does not exist", key_item_name)
                    exitcode = itemcount
            else:
                logger.info("skip OH item %s - for action %s",
                            key_item_name, action)

        if exitcode != 0:
            return exitcode

        if not found_action:
            logger.error("Did not find action %s", action)


IkeaZigbeeDevices()
