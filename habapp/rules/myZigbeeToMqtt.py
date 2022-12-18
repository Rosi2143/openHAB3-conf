import logging  # required for extended logging
import datetime
import time

import HABApp
from HABApp.core.events import ValueUpdateEvent, ValueUpdateEventFilter
from HABApp.mqtt.items import MqttItem
from HABApp.openhab.items import SwitchItem, NumberItem, DatetimeItem
from HABApp.openhab.events import ItemStateChangedEvent, ItemStateChangedEventFilter

log = logging.getLogger('Mqtt')


class zigbee2Mqtt_Bridge(HABApp.Rule):
    """handles items from and commands to the zigbee2Mqtt bridge"""

    def __init__(self):
        """initialize the Zigbee2MQTT bridge handler"""
        super().__init__()

        # map to convert MQTT states to OH switch item states and vise versa
        self.stateMap = {'False': 'OFF',
                         'True': 'ON',
                         'false': 'OFF',
                         'true': 'ON',
                         'ON': "true",
                         'OFF': "false"
                         }
        # base topic of MQTT brige information
        self.mqtt_base_topic = 'zigbee2mqtt/bridge/'
        # MQTT topic for bridge info
        self.mqtt_base_info = self.mqtt_base_topic + 'info'
        parmFile = 'ikea_param_file'
        # array of maps of all MQTT item read from parameter file
        self.mqttitems = {}
        self.mqttitems['BewegungsMelder'] = HABApp.DictParameter(
            parmFile, 'MotionDetectors', default_value=None)
        self.mqttitems['Licht'] = HABApp.DictParameter(
            parmFile, 'Lights', default_value=None)
        self.mqttitems['FernBedienung'] = HABApp.DictParameter(
            parmFile, 'RemoteControls', default_value=None)

        # item definitions
        # MQTT topic for requests info
        self.mqtt_base_request_topic = self.mqtt_base_topic + 'request/'
        # MQTT topic for responses info
        self.mqtt_base_response_topic = self.mqtt_base_topic + 'response/'
        # MQTT item send requestToJoin message
        self.mqtt_permitToJoin_request_item = MqttItem.get_create_item(
            self.mqtt_base_request_topic + "permit_join")
        # MQTT item read requestToJoin response
        self.mqtt_permitToJoin_response_item = MqttItem.get_create_item(
            self.mqtt_base_response_topic + "permit_join")
        # OpenHAB item to trigger permitToJoin
        self.oh_permitToJoin_State = SwitchItem.get_item(
            'Zigbee2Mqtt_PermitJoin')
        # OpenHAB item for permitToJoin timeout
        self.oh_permitToJoin_Timeout = NumberItem.get_item(
            'Zigbee2Mqtt_PermitJoin_Timeout')
        # OpenHAB item to store remaining permitToJoin time
        self.oh_permitToJoin_TimeRemain = NumberItem.get_item(
            'Zigbee2Mqtt_PermitJoin_TimeRemain')

        # MQTT item trigger healthcheck
        self.mqtt_healthCheck_request_item = MqttItem.get_create_item(
            self.mqtt_base_request_topic + "health_check")
        # MQTT item to read healthcheck response
        self.mqtt_healthCheck_response_item = MqttItem.get_create_item(
            self.mqtt_base_response_topic + "health_check")
        # OpenHAB item to trigger health check
        self.oh_healthCheck_State = SwitchItem.get_item('Zigbee2Mqtt_Health')
        self.run.every(
            start_time=datetime.timedelta(seconds=10),
            interval=datetime.timedelta(seconds=600),
            callback=self.trigger_health_check
        )

        # OpenHAB item to trigger creation of network map
        self.oh_networkMap_request_State = SwitchItem.get_item(
            'Zigbee2Mqtt_NetworkMap')
        # MQTT item trigger creation of network map
        self.mqtt_networkMap_request_item = MqttItem.get_create_item(
            self.mqtt_base_request_topic + "networkmap")
        # MQTT item to read network map response
        self.mqtt_networkMap_response_item = MqttItem.get_create_item(
            self.mqtt_base_response_topic + "networkmap")
        # OpenHAB item to save the date of the last network map check
        self.mqtt_networkMap_update = DatetimeItem.get_item(
            'Zigbee2Mqtt_NetworkMap_Update')
        self.run.on_day_of_week(
            time=datetime.time(4, 25, 46),
            weekdays=['Mon'],
            callback=self.trigger_networkmap_update)

        # MQTT item to trigger ota update for the selected item
        self.mqtt_TriggerUpdate_request_item = MqttItem.get_create_item(
            self.mqtt_base_request_topic + "device/ota_update/update")

        # MQTT item to trigger bridge restart
        self.mqtt_BridgeRestart_request_item = MqttItem.get_create_item(
            self.mqtt_base_request_topic + "restart")

        # OpenHAB item to trigger the bridge restart
        self.oh_RestartBridge_State = SwitchItem.get_item(
            'Zigbee2Mqtt_Restart_Bridge')

        # event registration
        self.listen_event(self.mqtt_base_info,
                          self.info_topic_updated, ValueUpdateEventFilter())

        self.listen_event(self.mqtt_base_response_topic + "permit_join",
                          self.permitToJoin_topic_updated, ValueUpdateEventFilter())
        self.oh_permitToJoin_State.listen_event(
            self.on_PermitJoin, ItemStateChangedEventFilter())

        self.listen_event(self.mqtt_base_response_topic + "health_check",
                          self.healthCheck_topic_updated, ValueUpdateEventFilter())

        self.listen_event(self.mqtt_base_response_topic + "networkmap",
                          self.networkmap_topic_updated, ValueUpdateEventFilter())

        self.oh_networkMap_request_State.listen_event(
            self.on_RequestNetworkMap, ItemStateChangedEventFilter())

        self.oh_RestartBridge_State.listen_event(
            self.on_BridgeRestartRequest, ItemStateChangedEventFilter())

        itemcount = 0
        for types in self.mqttitems:
            for items in self.mqttitems[types].values():
                triggerUpdateName = types + items + "_TriggerUpdate"
                if not self.openhab.item_exists(triggerUpdateName):
                    if self.openhab.create_item(item_type="Switch", name=triggerUpdateName, label=triggerUpdateName, category="switch", groups=["Zigbee2Mqtt"]):
                        log.info(
                            f"created new item {triggerUpdateName}. Waiting till item is in registry")
                        waitCounter = 0
                        while (not self.openhab.item_exists(triggerUpdateName)) & (waitCounter < 5):
                            log.info(f"waiting {waitCounter} seconds")
                            time.sleep(1)

                (SwitchItem.get_item(triggerUpdateName)).listen_event(
                    self.on_TriggerUpdate, ItemStateChangedEventFilter())
                log.info(
                    f"register listener for {triggerUpdateName} item # {itemcount}")
                itemcount = itemcount + 1

        log.info('rule Zigbee2Mqtt_Bridge started')

# helpers
#########
    def OH_SwitchItem_Changed(self, oh_switchItem, new_value):
        """did the OpenHAB switch item change?"""

        if ((oh_switchItem.is_on() and new_value == "OFF") or (oh_switchItem.is_off() and new_value == "ON")):
            return True
        else:
            return False

# info topic
# https://www.zigbee2mqtt.io/guide/usage/mqtt_topics_and_messages.html#zigbee2mqtt-bridge-info
############
    def info_topic_updated(self, event):
        """the topic of bridge info has changed"""

        assert isinstance(event, ValueUpdateEvent), type(event)
        log.info(f"mqtt topic {event.name} updated to {event.value}")

        permitJoin = self.stateMap[str(event.value["permit_join"])]
        if self.OH_SwitchItem_Changed(self.oh_permitToJoin_State, permitJoin):
            self.oh_permitToJoin_State.oh_send_command(permitJoin)

        if "permit_join_timeout" in event.value:
            remaining_time = int(event.value["permit_join_timeout"])
            if (remaining_time % 5) == 0:
                self.oh_permitToJoin_TimeRemain.oh_send_command(remaining_time)
        else:
            if self.oh_permitToJoin_TimeRemain.get_value() != 0:
                self.oh_permitToJoin_TimeRemain.oh_send_command(0)

# permit_join
# https://www.zigbee2mqtt.io/guide/usage/mqtt_topics_and_messages.html#zigbee2mqtt-bridge-request-permit-join
#############
    def on_PermitJoin(self, event):
        """the OpenHAB item to trigger permitToJoin has changed"""

        assert isinstance(event, ItemStateChangedEvent)
        log.info(f"set {event.name} updated to {event.value}")
        if event.value == "ON":
            timeout = 30
            if self.item_exists("Zigbee2Mqtt_PermitJoin_Timeout"):
                timeout = NumberItem.get_item(
                    "Zigbee2Mqtt_PermitJoin_Timeout").get_value()
            publish_value = "{\"value\": true, \"time\": " + str(timeout) + "}"
            self.mqtt_permitToJoin_request_item.publish(publish_value)
        else:
            publish_value = "{\"value\": false}"

    def permitToJoin_topic_updated(self, event):
        """the topic of permitToJoin has changed"""

        assert isinstance(event, ValueUpdateEvent), type(event)
        log.info(f"mqtt topic {event.name} updated to {event.value}")

# health check
# https://www.zigbee2mqtt.io/guide/usage/mqtt_topics_and_messages.html#zigbee2mqtt-bridge-request-health-check
##############
    def trigger_health_check(self):
        """the OpenHAB item to trigger HealthCheck has changed"""

        self.mqtt_healthCheck_request_item.publish("")

    def healthCheck_topic_updated(self, event):
        """the topic of bridge health check has changed"""

        assert isinstance(event, ValueUpdateEvent), type(event)
        log.info(f"mqtt topic {event.name} updated to {event.value}")
        if "data" in event.value:
            if "healthy" in event.value["data"]:
                self.oh_healthCheck_State.oh_send_command(
                    self.stateMap[str(event.value["data"]["healthy"])])

# networkMap
# https://www.zigbee2mqtt.io/guide/usage/mqtt_topics_and_messages.html#zigbee2mqtt-bridge-request-networkmap
##############

    def on_RequestNetworkMap(self, event):
        """helper function to trigger generation of network map"""

        assert isinstance(event, ItemStateChangedEvent)
        log.info(f"set {event.name} updated to {event.value}")
        if event.value == "ON":
            self.trigger_networkmap_update()
        else:
            publish_value = "{\"value\": false}"

    def trigger_networkmap_update(self):
        """the OpenHAB item to trigger creation of network Map has changed"""

        self.mqtt_networkMap_request_item.publish(
            "{\"type\": \"graphviz\", \"routes\": false}")

    def networkmap_topic_updated(self, event):
        """the topic of generated network map has changed"""

        assert isinstance(event, ValueUpdateEvent), type(event)
        log.info(f"mqtt topic {event.name} updated to {event.value}")
        if "data" in event.value:
            if "value" in event.value["data"]:
                digraph = "<details>\n<summary></summary>\nzigbee_networkmap\n"
                digraph = digraph + str(event.value["data"]["value"])
                digraph = digraph + "}\nzigbee_networkmap\n</details>\n"
                digraph = digraph.replace("\\n", '\n').replace("\\\"", "\"")
                with open("/home/openhabian/git/public_files/mqtt_networkmap.svg", "w") as text_file:
                    text_file.write(digraph)
#            subprocess.run(args=["./upload_mqtt_networkmap.sh"],\
#                           cwd="/home/openhabian/git/public_files/",\
#                           check=True,\
#                           shell=True,\
#                           capture_output=True)
        self.mqtt_networkMap_update.oh_send_command(datetime.datetime.now())

# bridge restart request
    def on_BridgeRestartRequest(self, event):
        """the OpenHAB item to request a bridge restart has changed"""

        assert isinstance(event, ItemStateChangedEvent)
        log.info(f"set {event.name} updated to {event.value}")
        if event.value == "ON":
            self.mqtt_BridgeRestart_request_item.publish("")
        else:
            publish_value = "{\"value\": false}"


# firmware update
# https://www.zigbee2mqtt.io/guide/usage/ota_updates.html#automatic-checking-for-available-updates
#############

    def on_TriggerUpdate(self, event):
        """the OpenHAB item to trigger an device update has changed"""

        assert isinstance(event, ItemStateChangedEvent)
        log.info(f"set {event.name} updated to {event.value}")
        if event.value == "ON":
            deviceName = (event.name).replace("_TriggerUpdate", "")
            publish_value = "IKEA/"
            if (deviceName.find("Licht") != -1):
                publish_value = publish_value + "Lampe/" + \
                    deviceName.replace("Licht", "")
            if (deviceName.find("FernBedienung") != -1):
                publish_value = publish_value + "FernBedienung/" + \
                    deviceName.replace("FernBedienung", "")
            if (deviceName.find("BewegungsMelder") != -1):
                publish_value = publish_value + "BewegungsMelder/" + \
                    deviceName.replace("BewegungsMelder", "")

            log.info(f"trigger update for {deviceName}")
            self.mqtt_TriggerUpdate_request_item.publish(
                "{\"id\": \"" + publish_value + "\"}")
        else:
            publish_value = "{\"value\": false}"


# zigbee2Mqtt_Bridge()
