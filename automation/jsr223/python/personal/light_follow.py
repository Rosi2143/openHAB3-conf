"""
makes other light(s) follow a leading light
"""

from core.rules import rule
from core.triggers import when


@rule("LightFollow: Office",
      description="handle office lights",
      tags=["itemchange", "light follow", "office"])
@when("Item LichtBuero_State changed")
def office_light_following(event):
    """make all office lights follow the main light"""

    office_light_following.log.info(
        "rule fired because of %s", event.itemName)

    events.sendCommand("eLichtBuero_Lampe_State", str(event.itemState))


@rule("LightFollow: Workshop",
      description="handle workshop lights",
      tags=["itemchange", "light follow", "workshop"])
@when("Item LichtWerkstatt_State changed")
def workshop_light_following(event):
    """handle daylight start event"""

    workshop_light_following.log.info(
        "rule fired because of %s", event.itemName)
    events.sendCommand("SteckdoseWerkstatt_State", str(event.itemState))
