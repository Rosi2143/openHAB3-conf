"""
This script handles Homematic-ip devices with special needs.
"""
# log:set INFO jsr223.jython.HomematicIP

from core.log import logging, LOG_PREFIX
from core.rules import rule
from core.triggers import when


@rule("HomematicIP: ShedDoor",
      description="handle shed door state",
      tags=["itemchange", "HomematicIP", "door"])
@when("Item TuerSchuppen_OpenState changed")
def homematic_ip_shed_door(event):
    """
    set light of shed

    Args:
        event (_type_): triggering event
    """
    homematic_ip_shed_door.log.info(
        "rule fired because of %s %s --> %s", event.itemName, event.oldItemState, event.itemState)

    if event.itemState == "OPEN":
        events.postUpdate("Schuppen_State", "ON")
    else:
        events.postUpdate("Schuppen_State", "OFF")


@rule("HomematicIP: ring detection",
      description="handle activation of door bell",
      tags=["channeltriggered", "HomematicIP", "doorbell"])
@when("Channel homematic:HmIP-DSD-PCB:homematicBridge-90f3312b69:0026DBE998F796:1#BUTTON triggered SHORT_PRESS")
def homematic_ip_ring_start(event):
    """
    handle press on door bell

    Args:
        event (_type_): triggering event
    """

    homematic_ip_ring_start.log.info(
        "rule fired")

    events.sendCommand("HabPanelDashboardName", "CameraSnap")
    events.sendCommand("HABPanel_Command", "SCREEN_ON")
    events.sendCommand("HabPanelDashboardNameExp", "ON")
    events.sendCommand("KlingelerkennungFlur_StoreState", "ON")


@rule("HomematicIP: ring detection ends",
      description="handle deactivation of door bell",
      tags=["itemchange", "HomematicIP", "doorbell"])
@when("Item KlingelerkennungFlur_StoreState changed to OFF")
def homematic_ip_ring_end(event):
    """
    door bell status was reset

    Args:
        event (_type_): triggering event
    """

    homematic_ip_ring_end.log.info(
        "rule fired")

    events.sendCommand("HabPanelDashboardName", "Erdgeschoss")

MAX_ALLOWED_TEMP = 27
NEW_ALLOWED_TEMP = 20
OVERHEAT_STRING = "_HitzeSchutzTimer"

@rule("HomematicIP: OverHeatProtectionStart",
      description="start timer to prevent too high temperatures",
      tags=["memberchange", "HomematicIP", "overheat"])
@when("Member of gThermostate_SetPointModes changed")
def homematic_overheat_protection_start(event):
    """
    make sure the temperature is not too high for too long

    Args:
        event (_type_): triggering event
    """

    homematic_overheat_protection_start.log.info(
        "rule fired because of %s %s --> %s", event.itemName, event.oldItemState, event.itemState)

    set_temp = event.itemState.intValue()

    if set_temp >= MAX_ALLOWED_TEMP:
        timer_item_name = event.itemName + OVERHEAT_STRING
        timer_item = itemRegistry.getItems(timer_item_name)
        if timer_item == []:
            homematic_overheat_protection_start.log.info("TimerItem: " + timer_item.name + " does not exist.")
        else:
            events.sendCommand(timer_item, "ON")

@rule("HomematicIP: OverHeatProtectionEnd",
      description="end of timer to prevent too high temperatures",
      tags=["memberchange", "HomematicIP", "overheat"])
@when("Member of gThermostate_HitzeSchutzTimer changed to OFF")
def homematic_overheat_protection_end(event):
    """
    set temperature back to "normal" after the timeout

    Args:
        event (_type_): triggering event
    """

    homematic_overheat_protection_end.log.info(
        "rule fired because of %s %s --> %s", event.itemName, event.oldItemState, event.itemState)

    item_name = event.itemName.replace(OVERHEAT_STRING, "")
    set_temp = items[item_name].intValue()
    new_temp = str(NEW_ALLOWED_TEMP)

    if set_temp >= MAX_ALLOWED_TEMP:
        homematic_overheat_protection_end.log.info("Reset: " + item_name + " to lower temperature of " + new_temp + "°C.")
        events.sendCommand(item_name, new_temp)
