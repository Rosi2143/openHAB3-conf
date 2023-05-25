"""
This script handles HABPanel notification items.
"""
# log:set INFO jsr223.jython.notifications

from core.log import logging, LOG_PREFIX
from core.rules import rule
from core.triggers import when


@rule("HABPanelNotification: first floor lights",
      description="handle light state if first floor",
      tags=["itemchange", "habpanel", "notifications", "lights"])
@when("Item gLichterObergeschoss changed")
def habpanel_notifications_first_floor_lights(event):
    """
    notification for first floor lights

    Args:
        event (_type_): triggering event
    """
    habpanel_notifications_first_floor_lights.log.info(
        "rule fired because of %s %s --> %s", event.itemName, event.oldItemState, event.itemState)

    events.postUpdate("LightNotification_FF", str(event.itemState))


@rule("HABPanelNotification: ground floor lights",
      description="handle light state if ground floor",
      tags=["itemchange", "habpanel", "notifications", "lights"])
@when("Item gLichterErdgeschoss changed")
def habpanel_notifications_ground_floor_lights(event):
    """
    notification for ground floor lights

    Args:
        event (_type_): triggering event
    """
    habpanel_notifications_ground_floor_lights.log.info(
        "rule fired because of %s %s --> %s", event.itemName, event.oldItemState, event.itemState)

    events.postUpdate("LightNotification_GF", str(event.itemState))


@rule("HABPanelNotification: basement lights",
      description="handle light state if basement",
      tags=["itemchange", "habpanel", "notifications", "lights"])
@when("Item gLichterKeller changed")
def habpanel_notifications_basement_lights(event):
    """
    notification for basement lights

    Args:
        event (_type_): triggering event
    """
    habpanel_notifications_basement_lights.log.info(
        "rule fired because of %s %s --> %s", event.itemName, event.oldItemState, event.itemState)

    events.postUpdate("LightNotification_BM", str(event.itemState))


@rule("HABPanelNotification: security issue",
      description="handle security issues of home",
      tags=["itemchange", "habpanel", "notifications", "security"])
@when("Item gAussenTuerenen changed")
@when("Item gFenster changed")
@when("Item TuerWaschkueche_OpenState changed")
def habpanel_notifications_security_state(event):
    """
    notification for security state

    Args:
        event (_type_): triggering event
    """
    habpanel_notifications_security_state.log.info(
        "rule fired because of %s %s --> %s", event.itemName, event.oldItemState, event.itemState)

    if ((items["gAussenTueren"] != "OPEN")
        and (items["gFenster"] != "OPEN")
        and (items["TuerWaschkueche_OpenState"] != "OPEN")
        ):
        events.sendCommand("SomeExternalWindowsDoorsOpen", "OFF")
    else:
        events.sendCommand("SomeExternalWindowsDoorsOpen", "ON")


@rule("HABPanelNotification: thing offline state",
      description="handle offline state of things",
      tags=["itemchange", "habpanel", "notifications", "things"])
@when("Item gThingItems changed")
def habpanel_notifications_thing_state(event):
    """
    notification for security state

    Args:
        event (_type_): triggering event
    """
    habpanel_notifications_thing_state.log.info(
        "rule fired because of %s %s --> %s", event.itemName, event.oldItemState, event.itemState)

    if (items["gThingItems"] != "OFF"):
        events.sendCommand("ThingItems", "ON")
    else:
        events.sendCommand("ThingItems", "OFF")
