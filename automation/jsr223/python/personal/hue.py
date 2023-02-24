"""
This script handles constant offline problem of hue network.
"""
# log:set INFO jsr223.jython.Hue

from core.log import logging, LOG_PREFIX
from core.rules import rule
from core.triggers import when


@rule("Hue: BewegungsmelderLang",
      description="store state of MotionDetector",
      tags=["itemchange", "Hue", "motion"])
@when("Item BewegungsmelderErkerweg_Motion changed to ON")
@when("Item BewegungsmelderEinfahrt_Motion changed to ON")
def hue_motion_long(event):
    """
    start timeout for motion detect

    Args:
        event (_type_): triggering event
    """
    hue_motion_long.log.info(
        "rule fired because of %s %s --> %s", event.itemName, event.oldItemState, event.itemState)

    events.postUpdate(event.itemName + "Long", "ON")


@rule("Hue: handle outside lights offline problems",
      description="handle outside lights offline problems",
      tags=["cron", "Hue", "offline"])
@when("Time cron 15 2/5 * 1/1 * ? *")
def hue_offline_handler(event):
    """
    handle offline problems of outside lights

    Args:
        event (_type_): triggering event
    """

    hue_offline_handler.log.info(
        "rule fired")

    EinfahrtDunkel = items["eLichtSensorEinfahrt_Dunkel"]
    EinfahrtHell = items["eLichtSensorEinfahrt_Hell"]
    EinfahrtBewegung = items["BewegungsmelderErkerweg_MotionLong"]
    EinfahrtMax = items["Hue_Raum_Einfahrt_Max"]
    EinfahrtMin = items["Hue_Raum_Einfahrt_Min"]
    EinfahrtStatus = items["Hue_Raum_Einfahrt_Betrieb"]

    ErkerWegDunkel = items["eLichtSensorErkerWeg_Dunkel"]
    ErkerWegHell = items["eLichtSensorErkerWeg_Hell"]
    ErkerWegBewegung = items["BewegungsmelderErkerweg_MotionLong"]
    ErkerWegMax = items["Hue_Raum_Erkerweg_Max"]
    ErkerWegMin = items["Hue_Raum_Erkerweg_Min"]
    ErkerWegStatus = items["Hue_Raum_Erkerweg_Betrieb"]

    if (EinfahrtMax - EinfahrtMin) > 5:
        hue_offline_handler.log.error(
            "Diff in EinfahrtLights = %d", (EinfahrtMax - EinfahrtMin))
    if EinfahrtDunkel:
        events.sendCommand("Hue_Raum_Einfahrt_Betrieb", "ON")
        if EinfahrtBewegung:
            hue_offline_handler.log.info("EinfahrtLights activate Light")
            events.sendCommand("Hue_Raum_Einfahrt_Szene",
                               "6UGV4IHOks-kO5Y")  # Konzentrieren
        else:
            hue_offline_handler.log.info("EinfahrtLights de-activate Light")
            events.sendCommand("Hue_Raum_Einfahrt_Szene",
                               "l7Vupj3gn20HJds")  # Nachtlicht
    else:
        events.sendCommand("Hue_Raum_Einfahrt_Betrieb", "OFF")

    if (ErkerWegMax - ErkerWegMin) > 5:
        hue_offline_handler.log.error(
            "Diff in ErkerWegLights = %d", (ErkerWegMax - ErkerWegMin))
    if ErkerWegDunkel:
        events.sendCommand("Hue_Raum_Erkerweg_Betrieb", "ON")
        if ErkerWegBewegung:
            hue_offline_handler.log.info("ErkerWegLights activate Light")
            events.sendCommand("Hue_Raum_Erkerweg_Szene",
                               "n4M-9bfD2CIN3Zi")  # Konzentrieren
        else:
            hue_offline_handler.log.info("ErkerWegLights de-activate Light")
            events.sendCommand("Hue_Raum_Erkerweg_Szene",
                               "bx5CWjHdoLZPZYV")  # Nachtlicht
    else:
        events.sendCommand("Hue_Raum_Erkerweg_Betrieb", "OFF")
