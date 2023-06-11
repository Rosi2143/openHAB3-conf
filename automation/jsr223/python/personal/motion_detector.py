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
@when("Member of gBewegungsmelder_MotionState changed")
def motiondetect_generic(event):
    """switch lamps when motion is detected"""
    motiondetect_generic.log.info(
        "rule fired because of %s %s --> %s", event.itemName, event.oldItemState, event.itemState)

    light_item_name_map = {"LichtFlur_State": "LichtFlurKeller_State"}

    light_item_name = "Licht" + \
        str(event.itemName).replace("Bewegungsmelder",
                                    "").replace("_MotionState", "_State")
    if light_item_name in light_item_name_map:
        light_item_name = light_item_name_map[light_item_name]

    events.sendCommand(light_item_name, str(event.itemState))
