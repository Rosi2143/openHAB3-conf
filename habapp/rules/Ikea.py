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

        parmFile = 'ikea_param_file'
        # read the low bat threshold from the parameter file
        self.min_battery_charge = HABApp.Parameter(
            parmFile, 'min_battery_charge', default_value=20)
        # read the motion detectors from the parameter file
        self.MotionDetectors = HABApp.DictParameter(
            parmFile, 'MotionDetectors', default_value=None)
        # read the lights from the parameter file
        self.Lights = HABApp.DictParameter(
            parmFile, 'Lights', default_value=None)
        # read the remote controls from the parameter file
        self.RemoteControls = HABApp.DictParameter(
            parmFile, 'RemoteControls', default_value=None)

        # map to convert MQTT states to switch states
        self.stateMap = {'False': 'OFF',
                         'True': 'ON',
                         'false': 'OFF',
                         'true': 'ON'
                         }
        # hold the base path for the MQTT topic
        self.mqtt_base_topic = "zigbee2mqtt/IKEA/"

        for MotionDetector in self.MotionDetectors.values():
            mqtt_MotionDetector_topic = self.mqtt_base_topic + \
                'BewegungsMelder/' + MotionDetector
            self.listen_event(mqtt_MotionDetector_topic,
                              self.motion_detect_updated, ValueUpdateEventFilter())
            logger.info("added listener for " + mqtt_MotionDetector_topic)

        for RemoteControl in self.RemoteControls.values():
            mqtt_RemoteControl_topic = self.mqtt_base_topic + 'FernBedienung/' + RemoteControl
            self.listen_event(mqtt_RemoteControl_topic,
                              self.remote_control_updated, ValueUpdateEventFilter())
            logger.info("added listener for " + mqtt_RemoteControl_topic)

        validator = {
            'min_battery_charge': int,
            'MotionDetectors': {str: str},
            'RemoteControls': {str: str},
            'Lights': {str: str}
        }
        HABApp.parameters.set_file_validator(parmFile, validator)

        self.init_light()

        logger.info('rule IkeaZigbeeDevices started')

# helpers
#########
    def OH_SwitchItem_Changed(self, oh_switchItem, new_value):
        """helper function to check if a dimmer item has changed"""

        ret = False
        state = oh_switchItem.get_value("OFF")
        if (state == "None") or (state == None):
            ret = True
        else:
            if ((state == "ON" and new_value == "OFF") or (state == "OFF" and new_value == "ON")):
                ret = True
        logger.debug(
            f"OH_SwitchItem_Changed for {oh_switchItem.name} {ret} <-- {oh_switchItem.get_value()} vs. {new_value}")
        return ret

    def OH_DimmerItem_Changed(self, oh_dimmerItem, new_value):
        """helper function to check if a dimmer item has changed"""

        ret = False
        # consider conversion of dimmer to IKEA / *2.04
        value = int(oh_dimmerItem.get_value(0))
        if value == "None":
            ret = True
        else:
            if (abs(value - new_value) > 5):
                ret = True
        logger.debug(
            f"OH_DimmerItem_Changed for {oh_dimmerItem.name} {ret} <-- {value} vs. {new_value}")
        return ret

    def OH_NumberItem_Changed(self, oh_numberItem, new_value):
        """helper function to check if a number item has changed"""

        ret = False
        value = int(oh_numberItem.get_value(0))
        if value == "None":
            ret = True
        else:
            if (value != new_value):
                ret = True
        logger.debug(
            f"OH_NumberItem_Changed for {oh_numberItem.name} {ret} <-- {value} vs. {new_value}")
        return ret

    def extractMqttItemName(self, ohItemName):
        """helper function to extract the mqtt item name from the OH topic"""

        logger.debug(ohItemName)
        _ohItemName = ohItemName.split("_")[0]
        logger.debug(_ohItemName)
        _ohItemName = _ohItemName.replace("Licht", "")
        logger.debug(_ohItemName)
        return _ohItemName

    def extractOhItemName(self, mqttTopic):
        """helper function to extract the OH name from the MQTT topic"""

        logger.debug(mqttTopic)
        _mqttTopic = mqttTopic.split("/")[3]
        logger.debug(_mqttTopic)
        return _mqttTopic

    def switchitem_update(self, event):
        """callback function for changes in switch items"""

        assert isinstance(event, ItemStateEvent)
        logger.debug(f'received {event.name} <- {event.value}')
        mqttTopic = self.mqtt_base_topic + "Lampe/" + \
            self.extractMqttItemName(event.name) + "/set"
        mqttTopicValue = "{ \"state\": \"" + str(event.value) + "\"}"
        logger.info(mqttTopic + ": " + mqttTopicValue)
        self.mqtt.publish(mqttTopic, mqttTopicValue)

    def dimmeritem_update(self, event):
        """callback function for changes in dimmer items"""

        assert isinstance(event, ValueUpdateEvent)
        logger.debug(f'received {event.name} <- {event.value}')

        mqttName = self.extractMqttItemName(event.name)
        transitionItemValue = 0

        mqttTopic = self.mqtt_base_topic + "Lampe/" + \
            self.extractMqttItemName(event.name) + "/set"
        # value conversion see https://www.zigbee2mqtt.io/devices/LED1732G11.html#light
        mqttValue = int(event.value)
        if "_Dimmer" in event.name:
            mqttTopicValue = "{ \"brightness\": "
            mqttValue = int(mqttValue * 2.54)
        else:
            if "_ColorTemp" in event.name:
                mqttTopicValue = "{ \"color_temp\": "
                mqttValue = int(mqttValue * 2.04) + 250
            else:
                logger.error(
                    "wrong callback dimmeritem_update for " + event.name)
                return

        mqttTopicValue = mqttTopicValue + str(mqttValue)

        if self.openhab.item_exists("Licht" + mqttName + "_Transition"):
            transitionItemValue = NumberItem.get_item(
                "Licht" + mqttName + "_Transition").get_value(5)

        if transitionItemValue != 0:
            mqttTopicValue = mqttTopicValue + \
                ", \"transition\": " + str(int(transitionItemValue))

        mqttTopicValue = mqttTopicValue + "}"
        logger.info(mqttTopic + ": " + mqttTopicValue)
        self.mqtt.publish(mqttTopic, mqttTopicValue)

    def numberitem_update(self, event):
        """callback function for changes in number items"""

        assert isinstance(event, ValueUpdateEvent)
        logger.debug(f'received {event.name} <- {event.value}')

        mqttName = self.extractMqttItemName(event.name)

        mqttTopic = self.mqtt_base_topic + "Lampe/" + mqttName + "/set"
        value = int(event.value)
        if "_Dimmer" in event.name:
            mqttTopicValue = "{ \"brightness"
            value = int(value * 2.54)
        else:
            if "_ColorTemp" in event.name:
                mqttTopicValue = "{ \"color_temp"
                value = int(value * 2.04)
            else:
                logger.error(
                    "wrong callback numberitem_update for " + event.name)
                return

        if "_Step" in event.name:
            mqttTopicValue = mqttTopicValue + "_step"
        else:
            if "_Move" in event.name:
                mqttTopicValue = mqttTopicValue + "_move"
            else:
                logger.error(
                    "wrong callback numberitem_update for " + event.name)
                return

        mqttTopicValue = mqttTopicValue + "\": " + str(value) + "}"
        logger.info(mqttTopic + ": " + mqttTopicValue)
        self.mqtt.publish(mqttTopic, mqttTopicValue)

    def stringitem_update(self, event):
        """callback function for changes in string items"""

        assert isinstance(event, ValueUpdateEvent)
        logger.debug(f'received {event.name} <- {event.value}')

        mqttName = self.extractMqttItemName(event.name)

        mqttTopic = self.mqtt_base_topic + "Lampe/" + mqttName + "/set"
        if "_ColorTemp_String" in event.name:
            mqttTopicValue = "{ \"color_temp"
        else:
            if "_Effect" in event.name:
                mqttTopicValue = "{ \"effect"
            else:
                logger.error(
                    "wrong callback stringitem_update for " + event.name)
                return

        mqttTopicValue = mqttTopicValue + "\": \"" + str(event.value) + "\"}"

        logger.info(mqttTopic + ": " + mqttTopicValue)
        self.mqtt.publish(mqttTopic, mqttTopicValue)

###############################################################################
# Ambient White Lights
###############################################################################

    def init_light(self):
        """"initialize the light elements

        register to OpenHAB items
        register to MQTT topics
        see https://www.zigbee2mqtt.io/devices/LED1545G12.html"""

        for Light in self.Lights.values():
            stateItemName = "Licht" + Light + "_State"
            if self.openhab.item_exists(stateItemName):
                switchItem = SwitchItem.get_item(stateItemName)
                switchItem.listen_event(
                    self.switchitem_update, ItemStateEventFilter())
            else:
                logger.error(f"{stateItemName} does not exist")

            dimmerItemName = "Licht" + Light + "_Dimmer"
            if self.openhab.item_exists(dimmerItemName):
                dimmerItem = DimmerItem.get_item(dimmerItemName)
                dimmerItem.listen_event(
                    self.dimmeritem_update, ItemStateEventFilter())
            else:
                logger.error(f"{dimmerItemName} does not exist")

            dimmerMoveItemName = "Licht" + Light + "_Dimmer_Move"
            if self.openhab.item_exists(dimmerMoveItemName):
                dimmerMoveItem = NumberItem.get_item(dimmerMoveItemName)
                dimmerMoveItem.listen_event(
                    self.numberitem_update, ItemStateEventFilter())
            else:
                logger.error(f"{dimmerMoveItemName} does not exist")

            dimmerStepItemName = "Licht" + Light + "_Dimmer_Step"
            if self.openhab.item_exists(dimmerStepItemName):
                dimmerStepItem = NumberItem.get_item(dimmerStepItemName)
                dimmerStepItem.listen_event(
                    self.numberitem_update, ItemStateEventFilter())
            else:
                logger.error(f"{dimmerStepItemName} does not exist")

            colorTempItemName = "Licht" + Light + "_ColorTemp"
            if self.openhab.item_exists(colorTempItemName):
                colorTempItem = DimmerItem.get_item(colorTempItemName)
                colorTempItem.listen_event(
                    self.dimmeritem_update, ItemStateEventFilter())
            else:
                logger.error(f"{colorTempItemName} does not exist")

            colorTempStringItemName = "Licht" + Light + "_ColorTemp_String"
            if self.openhab.item_exists(colorTempStringItemName):
                colorTempStringItem = StringItem.get_item(
                    colorTempStringItemName)
                colorTempStringItem.listen_event(
                    self.stringitem_update, ItemStateEventFilter())
            else:
                logger.error(f"{colorTempStringItemName} does not exist")

            colorTempMoveItemName = "Licht" + Light + "_ColorTemp_Move"
            if self.openhab.item_exists(colorTempMoveItemName):
                colorTempMoveItem = NumberItem.get_item(colorTempMoveItemName)
                colorTempMoveItem.listen_event(
                    self.numberitem_update, ItemStateEventFilter())
            else:
                logger.error(f"{colorTempMoveItemName} does not exist")

            colorTempStepItemName = "Licht" + Light + "_ColorTemp_Step"
            if self.openhab.item_exists(colorTempStepItemName):
                colorTempStepItem = NumberItem.get_item(colorTempStepItemName)
                colorTempStepItem.listen_event(
                    self.numberitem_update, ItemStateEventFilter())
            else:
                logger.error(f"{colorTempStepItemName} does not exist")

            effectItemName = "Licht" + Light + "_Effect"
            if self.openhab.item_exists(effectItemName):
                effectItem = StringItem.get_item(effectItemName)
                effectItem.listen_event(
                    self.stringitem_update, ItemStateEventFilter())
            else:
                logger.error(f"{effectItemName} does not exist")

            transitionItemName = "Licht" + Light + "_Transition"
            if self.openhab.item_exists(transitionItemName):
                transitionItem = NumberItem.get_item(transitionItemName)
                transitionItem.listen_event(
                    self.numberitem_update, ItemStateEventFilter())
            else:
                logger.error(f"{transitionItemName} does not exist")

            mqtt_Light_topic = self.mqtt_base_topic + 'Lampe/' + Light
            self.listen_event(mqtt_Light_topic,
                              self.light_updated, ValueUpdateEventFilter())
            logger.info("added listener for " + mqtt_Light_topic)

            logger.info("added listener for Light " + Light)
        logger.info('lights are setup')

    def light_updated(self, event):
        """handle changes in the mqtt topic of light elements"""

        assert isinstance(event, ValueUpdateEvent), type(event)
        logger.info(f"mqtt topic " + event.name +
                    " updated to " + str(event.value))

        if "state" in event.value:
            stateItemName = "Licht" + \
                self.extractOhItemName(event.name) + "_State"
            if self.openhab.item_exists(stateItemName):
                switchItem = SwitchItem.get_item(stateItemName)
                new_value = str(event.value["state"])
                if self.OH_SwitchItem_Changed(switchItem, new_value):
                    switchItem.oh_send_command(new_value)
                logger.info(f"state     : " + new_value)
            else:
                logger.error(f'item {stateItemName} does not exist')

        if "brightness" in event.value:
            dimmerItemName = "Licht" + \
                self.extractOhItemName(event.name) + "_Dimmer"
            if self.openhab.item_exists(dimmerItemName):
                dimmerItem = DimmerItem.get_item(dimmerItemName)
                new_value = int(int(event.value["brightness"]) / 2.54)
                if self.OH_DimmerItem_Changed(dimmerItem, new_value):
                    # IKEA https://www.zigbee2mqtt.io/devices/LED1732G11.html#light
                    # 0 ... 254
                    dimmerItem.oh_send_command(new_value)
                logger.info(f"brightness: " + str(new_value))
            else:
                logger.error(f'item {dimmerItemName} does not exist')

        if "color_temp" in event.value:
            colorTempItemName = "Licht" + \
                self.extractOhItemName(event.name) + "_ColorTemp"
            if self.openhab.item_exists(colorTempItemName):
                colorTempItem = DimmerItem.get_item(colorTempItemName)
                new_value = int((int(event.value["color_temp"]) - 250) / 2.04)
                if self.OH_DimmerItem_Changed(colorTempItem, new_value):
                    # IKEA https://www.zigbee2mqtt.io/devices/LED1732G11.html#light
                    # 250 ... 454
                    colorTempItem.oh_send_command(new_value)
                logger.info(f"colortemp : " + str(new_value))
            else:
                logger.error(f'item {colorTempItemName} does not exist')

        if "update" in event.value:
            if "state" in event.value["update"]:
                UpdateItemName = "Licht" + \
                    self.extractOhItemName(event.name) + "_UpdatePending"
                if self.openhab.item_exists(UpdateItemName):
                    UpdateItem = SwitchItem.get_item(UpdateItemName)
                    new_value = str(event.value["update"]["state"])
                    if new_value == "available":
                        new_value = "ON"
                    else:
                        new_value = "OFF"
                    if self.OH_SwitchItem_Changed(UpdateItem, new_value):
                        # IKEA https://www.zigbee2mqtt.io/devices/LED1732G11.html#light
                        # 250 ... 454
                        UpdateItem.oh_send_command(new_value)
                    logger.info(f"update    : " + new_value)
                else:
                    logger.error(f'item {UpdateItemName} does not exist')

###############################################################################
# Motion Detector
###############################################################################

    def motion_detect_updated(self, event):
        """handle changes in the MQTT topic for motion detectors."""

        assert isinstance(event, ValueUpdateEvent), type(event)

        batteryCharge = 100
        batteryWeak = False
        if 'battery' in event.value:
            batteryCharge = int(event.value['battery'])
        if (batteryCharge < self.min_battery_charge):
            batteryWeak = True

        occupancy = 'False'
        if 'occupancy' in event.value:
            occupancy = str(event.value['occupancy'])

        linkQuality = 100
        if 'linkquality' in event.value:
            linkQuality = event.value['linkquality']

        illuminanceAboveThreshold = False
        if 'illuminance_above_threshold' in event.value:
            illuminanceAboveThreshold = event.value['illuminance_above_threshold']

        updateAvailable = False
        if 'update' in event.value:
            if "available" == event.value["update"]["state"]:
                updateAvailable = True

        # see naming conventions in ikea.items
        topic_items = str(event.name).split('/')

        logger.debug(f"mqtt topic " + event.name +
                     " updated to\n" + json.dumps(event.value, indent=2))
        logger.info(f"Item       : " + topic_items[2] + topic_items[3])
        logger.info(f"MotionState: " + occupancy)
        logger.info(f"Battery    : " + str(batteryCharge))
        logger.info(f"BatteryWeak: " + str(batteryWeak))
        logger.info(f"LinkQuality: " + str(linkQuality))
        logger.info(f"LightState : " + str(illuminanceAboveThreshold))
        logger.info(f"FW Update  : " + str(updateAvailable))

        exitcode = 0
        if self.openhab.item_exists(topic_items[2] + topic_items[3] + "_BatteryStatus"):
            my_oh_item_batterystate = SwitchItem.get_item(
                topic_items[2] + topic_items[3] + "_BatteryStatus")
        else:
            logger.error(
                f"item " + topic_items[2] + topic_items[3] + "_BatteryStatus does not exist")
            exitcode = 1

        if self.openhab.item_exists(topic_items[2] + topic_items[3] + "_ChargingLevel"):
            my_oh_item_chargingLevel = NumberItem.get_item(
                topic_items[2] + topic_items[3] + "_ChargingLevel")
        else:
            logger.error(
                f"item " + topic_items[2] + topic_items[3] + "_ChargingLevel does not exist")
            exitcode = 2

        if self.openhab.item_exists(topic_items[2] + topic_items[3] + "_UpdatePending"):
            my_oh_item_updatepending = SwitchItem.get_item(
                topic_items[2] + topic_items[3] + "_UpdatePending")
        else:
            logger.error(
                f"item " + topic_items[2] + topic_items[3] + "_UpdatePending does not exist")
            exitcode = 3

        if self.openhab.item_exists(topic_items[2] + topic_items[3] + "_MotionState"):
            my_oh_item_motionstate = SwitchItem.get_item(
                topic_items[2] + topic_items[3] + "_MotionState")
        else:
            logger.error(
                f"item " + topic_items[2] + topic_items[3] + "_MotionState does not exist")
            exitcode = 4

        if self.openhab.item_exists(topic_items[2] + topic_items[3] + "_MotionDetectState"):
            my_oh_item_motiondetectstate = SwitchItem.get_item(
                topic_items[2] + topic_items[3] + "_MotionDetectState")
        else:
            logger.error(
                f"item " + topic_items[2] + topic_items[3] + "_MotionDetectState does not exist")
            exitcode = 5

        if exitcode != 0:
            return exitcode

        my_oh_item_chargingLevel.oh_send_command(batteryCharge)
        my_oh_item_batterystate.oh_send_command(
            self.stateMap[str(batteryWeak)])
        my_oh_item_updatepending.oh_send_command(
            self.stateMap[str(updateAvailable)])
        my_oh_item_motionstate.oh_send_command(self.stateMap[str(occupancy)])
        my_oh_item_motiondetectstate.oh_send_command(
            self.stateMap[str(illuminanceAboveThreshold)])

###############################################################################
# Remote Controller
###############################################################################

    def remote_control_updated(self, event):
        """handle changes in MQTT topic for remote control switches"""

        assert isinstance(event, ValueUpdateEvent), type(event)

        batteryCharge = 100
        batteryWeak = False
        if 'battery' in event.value:
            batteryCharge = int(event.value['battery'])
        if (batteryCharge < self.min_battery_charge):
            batteryWeak = True

        action = 'none'
        if 'action' in event.value:
            action = str(event.value['action'])

        linkQuality = 100
        if 'linkquality' in event.value:
            linkQuality = event.value['linkquality']

        updateAvailable = False
        if 'update' in event.value:
            if "available" == event.value["update"]["state"]:
                updateAvailable = True

        # see naming conventions in ikea.items
        topic_items = str(event.name).split('/')

        logger.debug(f"mqtt topic " + event.name +
                     " updated to\n" + json.dumps(event.value, indent=2))
        logger.info(f"Item       : " + topic_items[2] + topic_items[3])
        logger.info(f"Action     : " + action)
        logger.info(f"Battery    : " + str(batteryCharge))
        logger.info(f"BatteryWeak: " + str(batteryWeak))
        logger.info(f"LinkQuality: " + str(linkQuality))
        logger.info(f"FW Update  : " + str(updateAvailable))

        exitcode = 0
        if self.openhab.item_exists(topic_items[2] + topic_items[3] + "_BatteryStatus"):
            my_oh_item_batterystate = SwitchItem.get_item(
                topic_items[2] + topic_items[3] + "_BatteryStatus")
        else:
            logger.error(
                f"item " + topic_items[2] + topic_items[3] + "_BatteryStatus does not exist")
            exitcode = 1

        if self.openhab.item_exists(topic_items[2] + topic_items[3] + "_ChargingLevel"):
            my_oh_item_chargingLevel = NumberItem.get_item(
                topic_items[2] + topic_items[3] + "_ChargingLevel")
        else:
            logger.error(
                f"item " + topic_items[2] + topic_items[3] + "_ChargingLevel does not exist")
            exitcode = 2

        if self.openhab.item_exists(topic_items[2] + topic_items[3] + "_UpdatePending"):
            my_oh_item_updatepending = SwitchItem.get_item(
                topic_items[2] + topic_items[3] + "_UpdatePending")
        else:
            logger.error(
                f"item " + topic_items[2] + topic_items[3] + "_UpdatePending does not exist")
            exitcode = 3

        if exitcode != 0:
            return exitcode

        if self.OH_NumberItem_Changed(my_oh_item_chargingLevel, batteryCharge):
            my_oh_item_chargingLevel.oh_send_command(batteryCharge)
        if self.OH_SwitchItem_Changed(my_oh_item_batterystate, self.stateMap[str(batteryWeak)]):
            my_oh_item_batterystate.oh_send_command(
                self.stateMap[str(batteryWeak)])
        if self.OH_SwitchItem_Changed(my_oh_item_updatepending, self.stateMap[str(updateAvailable)]):
            my_oh_item_updatepending.oh_send_command(
                self.stateMap[str(updateAvailable)])

        keypress_items = {"toggle": ["_MainButton", "ON"],
                          "brightness_up_click": ["_UpButton", "ON"],
                          "brightness_down_click": ["_DownButton", "ON"],
                          "arrow_left_click": ["_LeftButton", "ON"],
                          "arrow_right_click": ["_RightButton", "ON"],

                          "toggle_hold": ["_MainButton_Long", "ON"],
                          "brightness_up_hold": ["_UpButton_Long", "ON"],
                          "brightness_down_hold": ["_DownButton_Long", "ON"],
                          "arrow_left_hold": ["_LeftButton_Long", "ON"],
                          "arrow_right_hold": ["_RightButton_Long", "ON"],

                          "brightness_up_release": ["_UpButton_Long", "OFF"],
                          "brightness_down_release": ["_DownButton_Long", "OFF"],
                          "arrow_left_release": ["_LeftButton_Long", "OFF"],
                          "arrow_right_release": ["_RightButton_Long", "OFF"],

                          "on": ["_MainButton", "ON"],
                          "brightness_move_up": ["_MainButton_Long", "ON"],
                          "brightness_stop": ["_MainButton_Long", "OFF"],
                          }

        itemcount = 3
        found_action = False
        for key, item in keypress_items.items():
            logger.debug(f"check action for {action} for {key}")
            key_itemname = topic_items[2] + topic_items[3] + item[0]
            if action == key:
                itemcount = itemcount + 1
                if self.openhab.item_exists(key_itemname):
                    oh_keypress_item = SwitchItem.get_item(key_itemname)
                    logger.debug(
                        f"found action for {action} for {key}  :: {key_itemname} --> {item[1]}")
                    if self.OH_SwitchItem_Changed(oh_keypress_item, item[1]):
                        oh_keypress_item.oh_send_command(item[1])
                    found_action = True
                    break
                else:
                    logger.error(f"item " + key_itemname + " does not exist")
                    exitcode = itemcount
            else:
                logger.info(
                    f"skip OH item {key_itemname} - for action {action}")

        if exitcode != 0:
            return exitcode

        if not found_action:
            logger.error(f"Did not find action {action}")


# IkeaZigbeeDevices()
