"""
makes other light(s) follow a leading light
"""

from core.rules import rule
from core.triggers import when

light_follow_map = {
    "LichtBuero_State": ["LichtBuero_Lampe_State"],
    "LichtWerkstatt_State": ["SteckdoseWerkstatt_State"],
    "LichtSchlafzimmer_State": ["SteckdoseSchlafzimmer_State"],
    "LichtEsszimmer_State": ["SteckdoseHighboard_State"],
    "LichtKuecheDecke_State": ["LichtKuecheToaster_State"],
    "LichtBadDecke_State": ["LichtBadSpiegel_State"],
    "LichtTerrasseUnten_State": ["LichtGrillbereich_Helligkeit", "Brunnen_Brightness"],
}


@rule(
    "LightFollow: Generic",
    description="handle office lights",
    tags=["itemchange", "light follow", "office"],
)
@when("Member of gHauptLichter changed")
def generic_light_following(event):
    """make all office lights follow the main light"""

    generic_light_following.log.info("rule fired because of %s", event.itemName)

    if not event.itemName in light_follow_map:
        generic_light_following.log.error(
            "element %s not found in %s", event.itemName, light_follow_map
        )
    else:
        for light in light_follow_map[event.itemName]:
            generic_light_following.log.info("setting %s to %s", light, event.itemState)
            events.sendCommand(light, str(event.itemState))


@rule(
    "LightFollow: FrontDoor",
    description="turn lights on when Frontdoor opens",
    tags=["itemchange", "light follow", "front door"],
)
@when("Item TuerHaustuer_StateContact changed to OPEN")
def light_following_frontdoor(event):
    """turn frontdoor light ON when door opens"""

    light_following_frontdoor.log.info("rule fired because of %s", event.itemName)

    outside_light = float(str(items["BewegungsmelderHaustuer_Illumination"]))
    if outside_light < 10:
        events.sendCommand("LichtFlurErdgeschoss_State", "ON")
        events.sendCommand("LichtHaustuer_State", "ON")
        light_following_frontdoor.log.info("turned lights ON")
    else:
        light_following_frontdoor.log.info(
            "not dark enough outside (%d>=10)",
            outside_light,
        )


@rule(
    "LightFollow: UpperFloor Storage",
    description="turn lights on/off when Frontdoor opens/closes",
    tags=["itemchange", "light follow", "storage"],
)
@when("Item TuerKammer_OpenState changed")
def light_following_upper_storage(event):
    """make all office lights follow the main light"""

    light_following_upper_storage.log.info("rule fired because of %s", event.itemName)

    if str(event.itemState) == "OPEN":
        events.sendCommand("LichtKammer_State", "ON")
    else:
        events.sendCommand("LichtKammer_State", "OFF")
