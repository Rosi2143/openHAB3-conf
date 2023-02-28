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
            events.postUpdate("eLichtTerrasse_Pergola_Alle_State", toggle_map[items["eLichtTerrasse_Pergola_Alle_State"]])
        if event.itemName.contains("_Up_"):
            events.postUpdate("eLichtTerrasse_Pergola_Alle_Dimmer", "100")
        if event.itemName.contains("_Left_"):
            events.postUpdate("eLichtTerrasse_Pergola_Alle_ColorTemp", "0")
        if event.itemName.contains("_Right_"):
            events.postUpdate("eLichtTerrasse_Pergola_Alle_ColorTemp", "100")
        if event.itemName.contains("_Down_"):
            events.postUpdate("eLichtTerrasse_Pergola_Alle_Dimmer", "1")
    else:
        if event.itemName.contains("_MainButton"):
            events.postUpdate("eLichtTerrasse_Pergola_Alle_State", toggle_map[items["eLichtTerrasse_Pergola_Alle_State"]])
        if event.itemName.contains("_Up"):
            events.postUpdate("eLichtTerrasse_Pergola_Alle_Dimmer_Step", "20")
        if event.itemName.contains("_Left"):
            events.postUpdate("eLichtTerrasse_Pergola_Alle_ColorTemp_Step", "-20")
        if event.itemName.contains("_Right"):
            events.postUpdate("eLichtTerrasse_Pergola_Alle_ColorTemp_Step", "20")
        if event.itemName.contains("_Down"):
            events.postUpdate("eLichtTerrasse_Pergola_Alle_Dimmer_Step", "-20")
