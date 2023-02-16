"""
This script handles event triggers of the astro binding.
"""

from core.rules import rule
from core.triggers import when


@rule("Astro: Daylight Start",
      description="handle event Daylight::START",
      tags=["astro"])
@when("Channel astro:sun:local:daylight#event triggered START")
def astro_daylight_start(event):
    """
    handle daylight start event

    Args:
        event (_type_): triggering event
    """

    astro_daylight_start.log.info(
        "rule fired because of %s", event.event)


@rule("Astro: SunSet Start",
      description="handle event SunSet::START",
      tags=["astro"])
@when("Channel astro:sun:local:set#event triggered START")
def astro_sunset_start(event):
    """
    handle sunset start event

    Args:
        event (_type_): triggering event
    """

    astro_sunset_start.log.info(
        "rule fired because of %s", event.event)


@rule("Astro: AstroDusk Start",
      description="handle event AstroDusk::START +20",
      tags=["astro"])
@when("Channel astro:sun:local:astroDusk#event triggered START")
def astro_astrodusk_start(event):
    """
    handle astroDusk (+20min) start event

    Args:
        event (_type_): triggering event
    """

    astro_astrodusk_start.log.info(
        "rule fired because of %s", event.event)
