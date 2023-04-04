"""
This script handles motion detector mapping.
"""
# log:set INFO jsr223.jython.MotionDetect

from core.log import logging, LOG_PREFIX
from core.rules import rule
from core.triggers import when


@rule("generic Motion detector rule",
      description="set light for motion detector",
      tags=["memberchange", "MotionDetect"])
@when("Member of gBewegungsmelder_State changed")
def motiondetect_generic(event):
    """switch lamps when motion is detected"""
    motiondetect_generic.log.info(
        "rule fired because of %s %s --> %s", event.itemName, event.oldItemState, event.itemState)

    light_item_name_map = {"LichtFlur_State", "LichtFlurKeller_State"}

    light_item_name = "Licht" + \
        str(event.itemName).replace("Bewegungsmelder",
                                    "").replace("_MotionState", "_State")
    if light_item_name in light_item_name_map:
        light_item_name = light_item_name_map["light_item_name"]

    events.postUpdate(light_item_name, str(event.itemState))

# Homematic-IP


@rule("MotionDetect: FrontDoor",
      description="MotionDetector of FrontDoor",
      tags=["itemchange", "MotionDetect", "frontdoor"])
@when("Item BewegungsmelderHaustuer_Motion changed")
def motiondetect_frontdoor(event):
    """
    switch lamp with motion detect

    Args:
        event (_type_): triggering event
    """
    motiondetect_frontdoor.log.info(
        "rule fired because of %s %s --> %s", event.itemName, event.oldItemState, event.itemState)

    events.postUpdate("LichtHaustuer_State", str(event.itemState))


@rule("MotionDetect: BasementCorridor",
      description="MotionDetector of Basement Corridor",
      tags=["itemchange", "MotionDetect", "basementcorridor"])
@when("Item BewegungsmelderFlur_Motion changed")
def motiondetect_basement_corridor(event):
    """
    switch lamp with motion detect

    Args:
        event (_type_): triggering event
    """
    motiondetect_basement_corridor.log.info(
        "rule fired because of %s %s --> %s", event.itemName, event.oldItemState, event.itemState)

    events.postUpdate("LichtFlurKeller_State", str(event.itemState))
