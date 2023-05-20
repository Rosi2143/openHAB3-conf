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

    EinfahrtDunkel = items["LichtSensorEinfahrt_Dunkel"]
    EinfahrtBewegung = items["BewegungsmelderErkerweg_MotionLong"]
    EinfahrtMax = items["Hue_Raum_Einfahrt_Max"].intValue()
    EinfahrtMin = items["Hue_Raum_Einfahrt_Min"].intValue()

    ErkerWegDunkel = items["LichtSensorErkerWeg_Dunkel"]
    ErkerWegBewegung = items["BewegungsmelderErkerweg_MotionLong"]
    ErkerWegMax = items["Hue_Raum_Erkerweg_Max"].intValue()
    ErkerWegMin = items["Hue_Raum_Erkerweg_Min"].intValue()

    hue_offline_handler.log.info("rule fired: \n Einfahrt: Dunkel %s; Bewegung %s; Min %s; Max %s\nErkerWeg: Dunkel %s; Bewegung %s; Min %s; Max %s",
                                 EinfahrtDunkel, EinfahrtBewegung, EinfahrtMin, EinfahrtMax, ErkerWegDunkel, ErkerWegBewegung, ErkerWegMin, ErkerWegMax)

    if (EinfahrtMax - EinfahrtMin) > 5:
        hue_offline_handler.log.error(
            "Diff in EinfahrtLights = %d", (EinfahrtMax - EinfahrtMin))
    if EinfahrtDunkel == "ON":
        events.sendCommand("Hue_Raum_Einfahrt_Betrieb", "ON")
        if EinfahrtBewegung == "ON":
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
    if ErkerWegDunkel == "ON":
        events.sendCommand("Hue_Raum_Erkerweg_Betrieb", "ON")
        if ErkerWegBewegung == "ON":
            hue_offline_handler.log.info("ErkerWegLights activate Light")
            events.sendCommand("Hue_Raum_Erkerweg_Szene",
                               "n4M-9bfD2CIN3Zi")  # Konzentrieren
        else:
            hue_offline_handler.log.info("ErkerWegLights de-activate Light")
            events.sendCommand("Hue_Raum_Erkerweg_Szene",
                               "bx5CWjHdoLZPZYV")  # Nachtlicht
    else:
        events.sendCommand("Hue_Raum_Erkerweg_Betrieb", "OFF")
