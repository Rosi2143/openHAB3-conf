"""
This script handles event triggers of the astro binding.
"""

from core.rules import rule
from core.triggers import when


@rule(
    "Astro: SunRise Start",
    description="handle event SunRise::START",
    tags=["itemchange", "astro", "sunrise"],
)
@when("Channel astro:sun:local:rise#event triggered START")
def astro_sunrise_start(event):
    """
    handle sunrise start event

    Args:
        event (_type_): triggering event
    """

    astro_sunrise_start.log.info("rule fired because of %s", event.triggerEvent)

    astro_sunrise_start.log.info("Hue de-activate NightLight")
    events.sendCommand("Hue_Zone_Garten_Betrieb", "OFF")


@rule(
    "Astro: Daylight Start",
    description="handle event Daylight::START",
    tags=["itemchange", "astro", "daylight"],
)
@when("Channel astro:sun:local:daylight#event triggered START")
def astro_daylight_start(event):
    """
    handle daylight start event

    Args:
        event (_type_): triggering event
    """

    astro_daylight_start.log.info("rule fired because of %s", event.triggerEvent)


@rule(
    "Astro: SunSet Start",
    description="handle event SunSet::START",
    tags=["itemchange", "astro", "sunset"],
)
@when("Channel astro:sun:local:set#event triggered START")
def astro_sunset_start(event):
    """
    handle sunset start event

    Args:
        event (_type_): triggering event
    """

    astro_sunset_start.log.info("rule fired because of %s", event.triggerEvent)

    astro_sunset_start.log.info("Hue activate NightLight")
    events.sendCommand("Hue_Zone_Garten_Betrieb", "ON")
    events.sendCommand("Hue_Zone_Garten_Zone", "l7Vupj3gn20HJds")  # Nachtlicht


@rule(
    "Astro: AstroDusk Start",
    description="handle event AstroDusk::START +20",
    tags=["itemchange", "astro", "astrodusk"],
)
@when("Channel astro:sun:local:astroDusk#event triggered START")
def astro_astrodusk_start(event):
    """
    handle astroDusk (+20min) start event

    Args:
        event (_type_): triggering event
    """

    astro_astrodusk_start.log.info("rule fired because of %s", event.triggerEvent)

    if items["TuerWaschkueche_OpenState"] == "OPEN":
        events.sendCommand("SchlossWaschkueche_Fehler", "ON")
        astro_astrodusk_start.log.error("cannot lock the door -- as it is open")
    else:
        events.sendCommand("SchlossWaschkueche_LockTargetLevel", "LOCKED")

    # 1=mow, 2=return to dock, 3=pause
    if items["Bosch_Indego_Zustand_numerisch"] == 1:
        events.sendCommand["Bosch_Indego_Zustand_numerisch", 2]
        astro_astrodusk_start.log.error("Indego still mowing --> send home")
    else:
        astro_astrodusk_start.log.info("Indego not mowing --> OK")
