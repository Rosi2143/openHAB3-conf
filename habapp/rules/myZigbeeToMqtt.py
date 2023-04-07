"""Handle items / topic of Zigbee2MQTT bridge"""

import logging  # required for extended logging
import datetime
import time

import HABApp
from HABApp.core.events import ValueUpdateEvent, ValueUpdateEventFilter
from HABApp.core.events import ValueChangeEvent, ValueChangeEventFilter
from HABApp.mqtt.items import MqttItem
from HABApp.openhab.items import SwitchItem, NumberItem, DatetimeItem

log = logging.getLogger('Mqtt')


class Zigbee2MqttBridge(HABApp.Rule):
    """handles items from and commands to the zigbee2Mqtt bridge"""

    def __init__(self):
        """initialize the Zigbee2MQTT bridge handler"""
        super().__init__()

        # map to convert MQTT states to OH switch item states and vise versa
        self.state_map = {'FALSE': 'OFF',
                          'TRUE': 'ON',
                          'ON': "true",
                          'OFF': "false"
                          }
        # base topic of MQTT bridge information
        self.mqtt_base_topic = 'zigbee2mqtt/bridge/'
        # MQTT topic for bridge info
        self.mqtt_base_info = self.mqtt_base_topic + 'info'
        parm_file = 'ikea_param_file'
        # array of maps of all MQTT item read from parameter file
        self.mqtt_items = {}
        self.mqtt_items['Bewegungsmelder'] = HABApp.DictParameter(
            parm_file, 'MotionDetectors', default_value=None)
        self.mqtt_items['Licht'] = HABApp.DictParameter(
            parm_file, 'Lights', default_value=None)
        self.mqtt_items['Fernbedienung'] = HABApp.DictParameter(
            parm_file, 'RemoteControls', default_value=None)

        # item definitions
        # MQTT topic for requests info
        self.mqtt_base_request_topic = self.mqtt_base_topic + 'request/'
        # MQTT topic for responses info
        self.mqtt_base_response_topic = self.mqtt_base_topic + 'response/'
        # MQTT item send requestToJoin message
        self.mqtt_permit_to_join_request_item = MqttItem.get_create_item(
            self.mqtt_base_request_topic + "permit_join")
        # MQTT item read requestToJoin response
        self.mqtt_permit_to_join_response_item = MqttItem.get_create_item(
            self.mqtt_base_response_topic + "permit_join")
        # OpenHAB item to trigger permitToJoin
        self.oh_permit_to_join_state = SwitchItem.get_item(
            'Zigbee2Mqtt_PermitJoin')
        log.info('Zigbee2Mqtt_PermitJoin state: %s',
                 self.oh_permit_to_join_state.get_value())
        # OpenHAB item for permitToJoin timeout
        self.oh_permit_to_join_timeout = NumberItem.get_item(
            'Zigbee2Mqtt_PermitJoin_Timeout')
        log.info('Zigbee2Mqtt_PermitJoin_Timeout state: %s',
                 self.oh_permit_to_join_timeout.get_value())
        # OpenHAB item to store remaining permitToJoin time
        self.oh_permit_to_join_time_remain = NumberItem.get_item(
            'Zigbee2Mqtt_PermitJoin_TimeRemain')

        # MQTT item trigger healthcheck
        self.mqtt_health_check_request_item = MqttItem.get_create_item(
            self.mqtt_base_request_topic + "health_check")
        # MQTT item to read healthcheck response
        self.mqtt_health_check_response_item = MqttItem.get_create_item(
            self.mqtt_base_response_topic + "health_check")
        # OpenHAB item to trigger health check
        self.oh_health_check_state = SwitchItem.get_item('Zigbee2Mqtt_Health')
        self.run.every(
            start_time=datetime.timedelta(seconds=10),
            interval=datetime.timedelta(seconds=600),
            callback=self.trigger_health_check
        )

        # OpenHAB item to trigger creation of network map
        self.oh_network_map_request_state = SwitchItem.get_item(
            'Zigbee2Mqtt_NetworkMap')
        # MQTT item trigger creation of network map
        self.mqtt_network_map_request_item = MqttItem.get_create_item(
            self.mqtt_base_request_topic + "networkmap")
        # MQTT item to read network map response
        self.mqtt_network_map_response_item = MqttItem.get_create_item(
            self.mqtt_base_response_topic + "networkmap")
        # OpenHAB item to save the date of the last network map check
        self.mqtt_network_map_update = DatetimeItem.get_item(
            'Zigbee2Mqtt_NetworkMap_Update')
        self.run.on_day_of_week(
            time=datetime.time(4, 25, 46),
            weekdays=['Mon'],
            callback=self.trigger_networkmap_update)

        # MQTT item to trigger ota update for the selected item
        self.mqtt_trigger_update_request_item = MqttItem.get_create_item(
            self.mqtt_base_request_topic + "device/ota_update/update")

        # MQTT item to trigger bridge restart
        self.mqtt_bridge_restart_request_item = MqttItem.get_create_item(
            self.mqtt_base_request_topic + "restart")

        # OpenHAB item to trigger the bridge restart
        self.oh_restart_bridge_state = SwitchItem.get_item(
            'Zigbee2Mqtt_Restart_Bridge')

        # event registration
        self.listen_event(self.mqtt_base_info,
                          self.info_topic_updated, ValueChangeEventFilter())

        self.listen_event(self.mqtt_base_response_topic + "permit_join",
                          self.permit_to_join_topic_updated, ValueUpdateEventFilter())
        self.oh_permit_to_join_state.listen_event(
            self.on_permit_join, ValueUpdateEventFilter(value="ON"))

        self.listen_event(self.mqtt_base_response_topic + "health_check",
                          self.health_check_topic_updated, ValueUpdateEventFilter())

        self.listen_event(self.mqtt_base_response_topic + "networkmap",
                          self.networkmap_topic_updated, ValueUpdateEventFilter())
        self.oh_network_map_request_state.listen_event(
            self.on_request_network_map, ValueUpdateEventFilter(value="ON"))

        self.oh_restart_bridge_state.listen_event(
            self.on_bridge_restart_request, ValueUpdateEventFilter(value="ON"))

        itemcount = 0
        for types in self.mqtt_items:
            for items in self.mqtt_items[types].values():
                trigger_update_name = types + items + "_TriggerUpdate"
                if not self.openhab.item_exists(trigger_update_name):
                    if self.openhab.create_item(item_type="Switch",
                                                name=trigger_update_name,
                                                label=trigger_update_name,
                                                category="switch",
                                                groups=["Zigbee2Mqtt"]):
                        log.info(
                            "created new item %s. Waiting till item is in registry",
                            trigger_update_name)
                        wait_counter = 0
                        while (not self.openhab.item_exists(trigger_update_name)) & \
                                (wait_counter < 5):
                            log.info("waiting %s seconds", wait_counter)
                            time.sleep(1)

                (SwitchItem.get_item(trigger_update_name)).listen_event(
                    self.on_trigger_update)
                log.info(
                    "register listener for %s item # %s", trigger_update_name, itemcount)
                itemcount = itemcount + 1

        log.info('rule Zigbee2Mqtt_Bridge started')

# helpers
#########
    def oh_switch_item_changed(self, oh_switch_item, new_value):
        """did the OpenHAB switch item change?"""

        if ((oh_switch_item.is_on() and new_value == "OFF") or
                (oh_switch_item.is_off() and new_value == "ON")):
            return True
        else:
            return False

# info topic
# https://www.zigbee2mqtt.io/guide/usage/mqtt_topics_and_messages.html#zigbee2mqtt-bridge-info
############
    def info_topic_updated(self, event):
        """the topic of bridge info has changed"""

        assert isinstance(event, ValueChangeEvent), type(event)
        log.info("mqtt topic %s updated to %s (type = %s)",
                 event.name, event.value, type(event))

        permit_join = self.state_map[str(event.value["permit_join"]).upper()]
        if self.oh_switch_item_changed(self.oh_permit_to_join_state, permit_join):
            self.oh_permit_to_join_state.oh_send_command(permit_join)

        if permit_join == "ON":
            if "permit_join_timeout" in event.value:
                remaining_time = int(event.value["permit_join_timeout"])
                if (remaining_time % 5) == 0:
                    self.oh_permit_to_join_time_remain.oh_send_command(
                        remaining_time)
        else:
            if self.oh_permit_to_join_time_remain.get_value() != 0:
                self.oh_permit_to_join_time_remain.oh_send_command(0)

# permit_join
# https://www.zigbee2mqtt.io/guide/usage/mqtt_topics_and_messages.html#zigbee2mqtt-bridge-request-permit-join
#############
    def on_permit_join(self, event):
        """the OpenHAB item to trigger permitToJoin has changed"""

        log.info("set %s updated to %s (type = %s)",
                 event.name, event.value, type(event))
        assert isinstance(event, ValueUpdateEvent)

        if str(event.value) == "ON":
            timeout = 30
            if self.openhab.item_exists("Zigbee2Mqtt_PermitJoin_Timeout"):
                timeout = NumberItem.get_item(
                    "Zigbee2Mqtt_PermitJoin_Timeout").get_value()
            publish_value = "{\"value\": true, \"time\": " + str(timeout) + "}"
        else:
            publish_value = "{\"value\": false}"
        self.mqtt_permit_to_join_request_item.publish(publish_value)

    def permit_to_join_topic_updated(self, event):
        """the topic of permitToJoin has changed"""

        log.info("mqtt topic %s updated to %s (type = %s)",
                 event.name, event.value, type(event))
        assert isinstance(event, ValueUpdateEvent), type(event)

# health check
# https://www.zigbee2mqtt.io/guide/usage/mqtt_topics_and_messages.html#zigbee2mqtt-bridge-request-health-check
##############
    def trigger_health_check(self):
        """the OpenHAB item to trigger HealthCheck has changed"""

        self.mqtt_health_check_request_item.publish("")

    def health_check_topic_updated(self, event):
        """the topic of bridge health check has changed"""

        assert isinstance(event, ValueUpdateEvent), type(event)
        log.info("mqtt topic %s updated to %s (type = %s)",
                 event.name, event.value, type(event))

        if "data" in event.value:
            if "healthy" in event.value["data"]:
                self.oh_health_check_state.oh_send_command(
                    self.state_map[str(event.value["data"]["healthy"]).upper()])

# networkMap
# https://www.zigbee2mqtt.io/guide/usage/mqtt_topics_and_messages.html#zigbee2mqtt-bridge-request-networkmap
##############

    def on_request_network_map(self, event: ValueUpdateEvent):
        """helper function to trigger generation of network map"""

        log.info("set %s updated to %s (type = %s)",
                 event.name, event.value, type(event))
        assert isinstance(event, ValueUpdateEvent)

        if event.value == "ON":
            self.trigger_networkmap_update()
        else:
            log.error("Check the event filter")

    def trigger_networkmap_update(self):
        """the OpenHAB item to trigger creation of network Map has changed"""

        self.mqtt_network_map_request_item.publish(
            "{\"type\": \"graphviz\", \"routes\": true}")

    def networkmap_topic_updated(self, event):
        """the topic of generated network map has changed"""

        assert isinstance(event, ValueUpdateEvent), type(event)
        log.info("mqtt topic %s updated to %s (type = %s)",
                 event.name, event.value, type(event))

        map_file = "/home/openhabian/git/public_files/mqtt_networkmap.svg"
        if "data" in event.value:
            if "value" in event.value["data"]:
                digraph = str(event.value["data"]["value"])
                digraph = digraph.replace("\\n", '\n').replace("\\\"", "\"")
                with open(map_file, "w") as text_file:
                    text_file.write(digraph)
        self.mqtt_network_map_update.oh_send_command(datetime.datetime.now())
        log.info("Check http://www.webgraphviz.com/ to generate graph")
        log.info("Data are stored in %s.", map_file)

# bridge restart request
    def on_bridge_restart_request(self, event: ValueUpdateEvent):
        """the OpenHAB item to request a bridge restart has changed"""

        log.info("set %s updated to %s (type = %s)",
                 event.name, event.value, type(event))
        assert isinstance(event, ValueUpdateEvent)

        if event.value == "ON":
            self.mqtt_bridge_restart_request_item.publish("")
        else:
            publish_value = "{\"value\": false}"
            self.mqtt_bridge_restart_request_item.publish(publish_value)


# firmware update
# https://www.zigbee2mqtt.io/guide/usage/ota_updates.html#automatic-checking-for-available-updates
#############

    def on_trigger_update(self, event: ValueUpdateEvent):
        """the OpenHAB item to trigger an device update has changed"""

        log.info("set %s updated to %s (type = %s)",
                 event.name, event.value, type(event))
        assert isinstance(event, ValueUpdateEvent)

        if event.value == "ON":
            device_name = (event.name).replace("_TriggerUpdate", "")
            publish_value = "IKEA/"
            if device_name.find("Licht") != -1:
                publish_value = publish_value + "Lampe/" + \
                    device_name.replace("Licht", "")
            if device_name.find("Fernbedienung") != -1:
                publish_value = publish_value + "Fernbedienung/" + \
                    device_name.replace("Fernbedienung", "")
            if device_name.find("Bewegungsmelder") != -1:
                publish_value = publish_value + "Bewegungsmelder/" + \
                    device_name.replace("Bewegungsmelder", "")

            log.info("trigger update for %s", device_name)
            self.mqtt_trigger_update_request_item.publish(
                "{\"id\": \"" + publish_value + "\"}")
        else:
            publish_value = "{\"value\": false}"


Zigbee2MqttBridge()
