import logging  # required for extended logging

import HABApp
from HABApp.core.events import ValueUpdateEvent, ValueUpdateEventFilter
from HABApp.mqtt.items import MqttItem

log = logging.getLogger('Mqtt')


class ExampleMqttTestRule(HABApp.Rule):
    """test rule for MQTT from the examples"""

    def __init__(self):
        """initialize the example rule for MQTT.

            * Publish a MQTT item and register#
            * register for the topic and get a callback"""
        super().__init__()

#        self.run.every(
#            start_time=datetime.timedelta(seconds=10),
#            interval=datetime.timedelta(seconds=200),
#            callback=self.publish_rand_value
#        )
#
#        ## hold the MQTT topic to publish and subscribe
#        self.mqtt_test_topic = 'zigbee2mqtt/bridge/config'
#        ## item to publish data on MQTT
#        self.my_mqtt_item = MqttItem.get_create_item(self.mqtt_test_topic)
#        self.listen_event(self.mqtt_test_topic, self.topic_updated, ValueUpdateEventFilter())

        log.info('rule myMqttRule started')

    def publish_rand_value(self):
        """cyclically generate a random value and publish it to MQTT"""
        log.info('test mqtt_publish to ' + self.mqtt_test_topic)
        self.my_mqtt_item.publish(str(random.randint(0, 1000)))

    def topic_updated(self, event):
        """example callback for a changed NQTT topic"""
        assert isinstance(event, ValueUpdateEvent), type(event)
        log.info(f"mqtt topic " + self.mqtt_test_topic +
                 " updated to " + str(event.value))


ExampleMqttTestRule()
