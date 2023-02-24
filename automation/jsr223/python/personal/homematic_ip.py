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
def homematic_ip_ring(event):
    """
    handle press on door bell

    Args:
        event (_type_): triggering event
    """

    homematic_ip_ring.log.info(
        "rule fired")

    events.sendCommand("HabPanelDashboardName", "CameraSnap")
    events.sendCommand("HABPanel_Command", "SCREEN_ON")
    events.sendCommand("HabPanelDashboardNameExp", "ON")
    events.sendCommand("KlingelerkennungFlur_StoreState", "ON")


@rule("HomematicIP: ring detection ends",
      description="handle deactivation of door bell",
      tags=["itemchange", "HomematicIP", "doorbell"])
@when("Item KlingelerkennungFlur_StoreState changed to OFF")
def homematic_ip_ring(event):
    """
    door bell status was reset

    Args:
        event (_type_): triggering event
    """

    homematic_ip_ring.log.info(
        "rule fired")

    events.sendCommand("HabPanelDashboardName", "Erdgeschoss")
