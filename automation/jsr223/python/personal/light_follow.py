"""
makes other light(s) follow a leading light
"""

from core.rules import rule
from core.triggers import when

light_follow_map = {"LichtBuero_State": ["LichtBuero_Lampe_State"],
                    "LichtWerkstatt_State": ["SteckdoseWerkstatt_State"],
                    "LichtSchlafzimmer_State": ["SteckdoseSchlafzimmer_State"],
                    "LichtEsszimmer_State": ["SteckdoseHighboard_State"],
                    "LichtKuecheDecke_State": ["LichtKuecheToaster_State"],
                    "LichtBadDecke_State": ["LichtBadSpiegel_State"],
                    "LichtTerrasseUnten_State": ["LichtGrillbereich_Helligkeit", "Brunnen_Brightness"]
                    }


@rule("LightFollow: Generic",
      description="handle office lights",
      tags=["itemchange", "light follow", "office"])
@when("Member of gHauptLichter changed")
def generic_light_following(event):
    """make all office lights follow the main light"""

    generic_light_following.log.info(
        "rule fired because of %s", event.itemName)

    if not event.itemName in light_follow_map:
        generic_light_following.log.error(
            "element %s not found in %s", event.itemName, light_follow_map)
    else:
        for light in light_follow_map[event.itemName]:
            generic_light_following.log.info(
                "setting %s to %s", light, event.itemState)
            events.sendCommand(
                light, str(event.itemState))
