"""
This script handles mqtt items.
"""
# log:set INFO jsr223.jython.mqtt

from core.log import logging, LOG_PREFIX
from core.rules import rule
from core.triggers import when

toggle_map = {"OFF": "ON",
              "ON": "OFF",
              "NULL": "ON"
              }


@rule("MQTT: Sleeping remote",
      description="handle buttons of remote control",
      tags=["itemchange", "mqtt", "remote"])
@when("Item FernbedienungSchlafzimmer_Main changed to ON")
@when("Item FernbedienungSchlafzimmer_Main_Long changed to ON")
def mqtt_sleeping_remote(event):
    """
    key of remote control

    Args:
        event (_type_): triggering event
    """
    mqtt_sleeping_remote.log.info(
        "rule fired because of %s %s --> %s", event.itemName, event.oldItemState, event.itemState)

    if "_Long" in event.itemName:
        events.postUpdate("gLichterKeller_State", "OFF")
    else:
        events.postUpdate("LichtGaestezimmer_State",
                          toggle_map[str(items["LichtGaestezimmer_State"])])


@rule("MQTT: Terrasse remote",
      description="handle buttons of remote control",
      tags=["itemchange", "mqtt", "remote"])
@when("Member of gFernbedienungTerrasse changed to ON")
def mqtt_terrasse_remote(event):
    """
    key of remote control

    Args:
        event (_type_): triggering event
    """
    mqtt_terrasse_remote.log.info(
        "rule fired because of %s %s --> %s", event.itemName, event.oldItemState, event.itemState)

    if "_Long" in event.itemName:
        if "_MainButton_" in event.itemName:
            events.postUpdate("eLichtTerrasse_Pergola_Alle_State",
                              toggle_map[str(items["eLichtTerrasse_Pergola_Alle_State"])])
        if "_Up_" in event.itemName:
            events.postUpdate("eLichtTerrasse_Pergola_Alle_Dimmer", "100")
        if "_Left_" in event.itemName:
            events.postUpdate("eLichtTerrasse_Pergola_Alle_ColorTemp", "0")
        if "_Right_" in event.itemName:
            events.postUpdate("eLichtTerrasse_Pergola_Alle_ColorTemp", "100")
        if "_Down_" in event.itemName:
            events.postUpdate("eLichtTerrasse_Pergola_Alle_Dimmer", "1")
    else:
        if "_MainButton" in event.itemName:
            events.postUpdate("eLichtTerrasse_Pergola_Alle_State",
                              toggle_map[str(items["eLichtTerrasse_Pergola_Alle_State"])])
        if "_Up" in event.itemName:
            events.postUpdate("eLichtTerrasse_Pergola_Alle_Dimmer_Step", "20")
        if "_Left" in event.itemName:
            events.postUpdate(
                "eLichtTerrasse_Pergola_Alle_ColorTemp_Step", "-20")
        if "_Right" in event.itemName:
            events.postUpdate(
                "eLichtTerrasse_Pergola_Alle_ColorTemp_Step", "20")
        if "_Down" in event.itemName:
            events.postUpdate("eLichtTerrasse_Pergola_Alle_Dimmer_Step", "-20")
