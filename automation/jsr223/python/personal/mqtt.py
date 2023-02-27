"""
This script handles mqtt items.
"""
# log:set INFO jsr223.jython.mqtt

from core.log import logging, LOG_PREFIX
from core.rules import rule
from core.triggers import when

toggle_map = {"OFF" : "ON",
              "ON" : "OFF"
             }

@rule("MQTT: Sleeping remote",
      description="handle buttons of remote control",
      tags=["itemchange", "mqtt", "remote"])
@when("Item RemoteControl_Sleeping_Main changed to ON")
@when("Item RemoteControl_Sleeping_Main_Long changed to ON")
def mqtt_sleeping_remote(event):
    """
    key of remote control

    Args:
        event (_type_): triggering event
    """
    mqtt_sleeping_remote.log.info(
        "rule fired because of %s %s --> %s", event.itemName, event.oldItemState, event.itemState)

    if event.itemName.contains("_Long"):
        events.postUpdate("gLichterKeller_State", "OFF")
    else:
        events.postUpdate("LichtGaestezimmer_State", toggle_map[items["LichtGaestezimmer_State"]])


@rule("MQTT: Terrasse remote",
      description="handle buttons of remote control",
      tags=["itemchange", "mqtt", "remote"])
@when("Member of eRemoteControl_Terrasse changed to ON")
def mqtt_terrasse_remote(event):
    """
    key of remote control

    Args:
        event (_type_): triggering event
    """
    mqtt_terrasse_remote.log.info(
        "rule fired because of %s %s --> %s", event.itemName, event.oldItemState, event.itemState)

    if event.itemName.contains("_Long"):
        if event.itemName.contains("_MainButton_"):
            pass
#            events.postUpdate("LichtGaestezimmer_State", toggle_map[items["LichtGaestezimmer_State"]])
        if event.itemName.contains("_Up_"):
            pass
#            events.postUpdate("LichtGaestezimmer_State", toggle_map[items["LichtGaestezimmer_State"]])
        if event.itemName.contains("_Left_"):
            pass
#            events.postUpdate("LichtGaestezimmer_State", toggle_map[items["LichtGaestezimmer_State"]])
        if event.itemName.contains("_Right_"):
            pass
#            events.postUpdate("LichtGaestezimmer_State", toggle_map[items["LichtGaestezimmer_State"]])
        if event.itemName.contains("_Down_"):
            pass
#            events.postUpdate("LichtGaestezimmer_State", toggle_map[items["LichtGaestezimmer_State"]])
    else:
        if event.itemName.contains("_MainButton"):
            pass
#            events.postUpdate("LichtGaestezimmer_State", toggle_map[items["LichtGaestezimmer_State"]])
        if event.itemName.contains("_Up"):
            pass
#            events.postUpdate("LichtGaestezimmer_State", toggle_map[items["LichtGaestezimmer_State"]])
        if event.itemName.contains("_Left"):
            pass
#            events.postUpdate("LichtGaestezimmer_State", toggle_map[items["LichtGaestezimmer_State"]])
        if event.itemName.contains("_Right"):
            pass
#            events.postUpdate("LichtGaestezimmer_State", toggle_map[items["LichtGaestezimmer_State"]])
        if event.itemName.contains("_Down"):
            pass
#            events.postUpdate("LichtGaestezimmer_State", toggle_map[items["LichtGaestezimmer_State"]])
