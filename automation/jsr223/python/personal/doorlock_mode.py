"""Example of python module statemachine: https://pypi.org/project/python-statemachine/"""

# log:set INFO jsr223.jython.door_lock_mode
# minimum version python-statemachine = 1.0.3

import sys
import os

from core.log import logging, LOG_PREFIX
from core.rules import rule
from core.triggers import when

OH_CONF = os.getenv('OPENHAB_CONF')

sys.path.append(os.path.join(OH_CONF, "automation/lib/python/personal"))
from door_lock_statemachine import door_lock_statemachine, get_state_machine_graph

log = logging.getLogger("{}.door_lock_mode".format(LOG_PREFIX))

DOOR_LOCK_STATE_MACHINE = door_lock_state_machine = door_lock_statemachine(
    "WaschKueche", log)


def set_mode_item(state):
    """set the door_lock_mode item """
    events.sendCommand("SchlossWaschkueche_Mode", state)


def is_dark_outside(sun_phase):
    """checks if it is dark outside"""
    if ((sun_phase == "NAUTIC_DUSK") | (sun_phase == "ASTRO_DUSK") |
            (sun_phase == "NIGHT") | (sun_phase == "ASTRO_DAWN") |
            (sun_phase == "NAUTIC_DAWN")
            ):
        return True
    else:
        return False


@rule("Door_Lock_statemachine_create",
      description="initialize the statemachines for door lock device",
      tags=["systemstart", "doorlock", "statemachines"])
@when("System started")
def initialize_door_lock_statemachine(event):
    """setup all statemachines for door lock device"""

    ThingName = "SchlossWaschkueche"

    # CONFIG_PENDING
    config_pending_state = itemRegistry.getItem(
        ThingName + "_ConfigPending").state
    initialize_door_lock_statemachine.log.info(
        "handling Config Pending: (" + str(config_pending_state) + ")")
    DOOR_LOCK_STATE_MACHINE.set_lock_error(
        DOOR_LOCK_STATE_MACHINE.CONFIG_PENDING, (config_pending_state == "ON"))
    DOOR_LOCK_STATE_MACHINE.send("tr_error_change")

    # ERROR_JAMMED
    error_jammed_state = itemRegistry.getItem(ThingName + "_ErrorJammed").state
    initialize_door_lock_statemachine.log.info(
        "handling Error Jammed: (" + str(error_jammed_state) + ")")
    DOOR_LOCK_STATE_MACHINE.set_lock_error(
        DOOR_LOCK_STATE_MACHINE.JAMMED, (error_jammed_state == "ON"))
    DOOR_LOCK_STATE_MACHINE.send("tr_error_change")

    # UNREACHABLE
    unreachable_state = itemRegistry.getItem(ThingName + "_Unreachable").state
    initialize_door_lock_statemachine.log.info(
        "handling Unreachable: (" + str(unreachable_state) + ")")
    DOOR_LOCK_STATE_MACHINE.set_lock_error(
        DOOR_LOCK_STATE_MACHINE.UNREACHABLE, (unreachable_state == "ON"))
    DOOR_LOCK_STATE_MACHINE.send("tr_error_change")

    # REPORTED_LOCK_STATE
    reported_lock_state = itemRegistry.getItem(ThingName + "_LockState").state
    initialize_door_lock_statemachine.log.info(
        "handling reported LockState: (" + str(reported_lock_state) + ")")
    DOOR_LOCK_STATE_MACHINE.set_reported_lock(str(reported_lock_state))
    DOOR_LOCK_STATE_MACHINE.send("tr_reported_lock_change")

    # DarkOutside
    dark_outside_state_state = itemRegistry.getItem(
        "Sonnendaten_Sonnenphase").state
    initialize_door_lock_statemachine.log.info(
        "handling DarkOutside: (" + str(dark_outside_state_state) + ")")
    DOOR_LOCK_STATE_MACHINE.set_dark_outside(
        is_dark_outside(str(dark_outside_state_state)))
    DOOR_LOCK_STATE_MACHINE.send("tr_dark_outside_change")

    # Presence
    presence_state = itemRegistry.getItem("gAnwesenheit").state
    initialize_door_lock_statemachine.log.info(
        "handling Presence: (" + str(presence_state) + ")")
    DOOR_LOCK_STATE_MACHINE.set_door_open((presence_state == "ON"))
    DOOR_LOCK_STATE_MACHINE.send("tr_presence_change")

    # DoorState
    door_open_state = itemRegistry.getItem("TuerWaschkueche_OpenState").state
    initialize_door_lock_statemachine.log.info(
        "handling DoorOpen: (" + str(door_open_state) + ")")
    DOOR_LOCK_STATE_MACHINE.set_door_open((door_open_state == "OPEN"))
    DOOR_LOCK_STATE_MACHINE.send("tr_door_state_change")

    # TerraceLight
    light_state = itemRegistry.getItem("LichtTerrasseUnten_State").state
    initialize_door_lock_statemachine.log.info(
        "handling Terrace Light: (" + str(light_state) + ")")
    DOOR_LOCK_STATE_MACHINE.set_light((light_state == "ON"))
    DOOR_LOCK_STATE_MACHINE.send("tr_error_change")

    set_mode_item(DOOR_LOCK_STATE_MACHINE.get_state_name())

    get_state_machine_graph(DOOR_LOCK_STATE_MACHINE)

    initialize_door_lock_statemachine.log.info("Done")

# ####################
# Rules
# ####################

# Check DarkOutside


@ rule("Door_Lock_DarkOutside_check",
       description="react on changes in SunData",
       tags=["itemchange", "doorlock", "statemachines", "darkoutside"])
@when("Item Sonnendaten_Sonnenphase changed")
def door_dark_outside_changes(event):
    """
    send event to DoorLock statemachine if DarkOutside changes
    Args:
        event (_type_): any DarkOutside item
    """
    door_dark_outside_changes.log.info(
        "rule fired because of %s %s --> %s", event.itemName, event.oldItemState, event.itemState)

    DOOR_LOCK_STATE_MACHINE.set_dark_outside(
        is_dark_outside(str(event.itemState)))
    DOOR_LOCK_STATE_MACHINE.send("tr_dark_outside_change")
    set_mode_item(DOOR_LOCK_STATE_MACHINE.get_state_name())

# Check DoorState


@rule("Door_Lock_DoorState_check",
      description="react on changes in DoorState",
      tags=["itemchange", "doorlock", "statemachines", "presence"])
@when("Item TuerWaschkueche_OpenState changed")
def door_lock_party_mode_changes(event):
    """
    send event to DoorLock statemachine if DoorState changes
    Args:
        event (_type_): any DoorState item
    """
    door_lock_party_mode_changes.log.info(
        "rule fired because of %s %s --> %s", event.itemName, event.oldItemState, event.itemState)

    DOOR_LOCK_STATE_MACHINE.set_door_open(str(event.itemState) == "ON")
    DOOR_LOCK_STATE_MACHINE.send("tr_door_state_change")
    set_mode_item(DOOR_LOCK_STATE_MACHINE.get_state_name())

# Check Errors


@rule("Door_Lock_Error_check",
      description="react on changes in error items",
      tags=["itemchange", "doorlock", "statemachines", "Errors"])
@when("Item SchlossWaschkueche_ConfigPending changed")
@when("Item SchlossWaschkueche_ErrorJammed changed")
@when("Item SchlossWaschkueche_Unreachable changed")
def door_lock_error_changes(event):
    """
    send event to DoorLock statemachine if error items change
    Args:
        event (_type_): any ErrorState item
    """
    door_lock_error_changes.log.info(
        "rule fired because of %s %s --> %s", event.itemName, event.oldItemState, event.itemState)

    errorType = ""
    if event.itemName.includes("ConfigPending"):
        errorType = DOOR_LOCK_STATE_MACHINE.CONFIG_PENDING
    elif event.itemName.includes("ErrorJammed"):
        errorType = DOOR_LOCK_STATE_MACHINE.JAMMED
    elif event.itemName.includes("Unreachable"):
        errorType = DOOR_LOCK_STATE_MACHINE.UNREACHABLE
    else:
        door_lock_error_changes.log.error("Unknown event %s", event.itemName)

    DOOR_LOCK_STATE_MACHINE.set_lock_error(
        errorType, str(event.itemState) == "ON")
    DOOR_LOCK_STATE_MACHINE.send("tr_error_change")
    set_mode_item(DOOR_LOCK_STATE_MACHINE.get_name(),
                  DOOR_LOCK_STATE_MACHINE.get_state_name())

# Check Light


@rule("Door_Lock_Light_check",
      description="react on changes in Light",
      tags=["itemchange", "doorlock", "statemachines", "light"])
@when("Item LichtTerrasseUnten_State changed")
def door_lock_light_changed(event):
    """
    send event to DoorLock statemachine if Light changes
    Args:
        event (_type_): any Light item
    """
    door_lock_light_changed.log.info(
        "rule fired because of %s %s --> %s", event.itemName, event.oldItemState, event.itemState)

    DOOR_LOCK_STATE_MACHINE.set_light(str(event.itemState) == "ON")
    DOOR_LOCK_STATE_MACHINE.send("tr_light_change")
    set_mode_item(DOOR_LOCK_STATE_MACHINE.get_state_name())

# Check Presence


@rule("DoorLock_Presence_check",
      description="react on changes in Presence",
      tags=["itemchange", "doorlock", "statemachines", "presence"])
@when("Item gAnwesenheit changed")
def door_lock_presence_changed(event):
    """
    send event to DoorLock statemachine if Presence changes
    Args:
        event (_type_): any Presence item
    """
    door_lock_presence_changed.log.info(
        "rule fired because of %s %s --> %s", event.itemName, event.oldItemState, event.itemState)

    DOOR_LOCK_STATE_MACHINE.set_presence(str(event.itemState) == "ON")
    DOOR_LOCK_STATE_MACHINE.send("tr_presence_change")
    set_mode_item(DOOR_LOCK_STATE_MACHINE.get_state_name())


# Check ReportedLock
@rule("Door_Lock_ReportedLock_check",
      description="react on changes in ReportedLock",
      tags=["itemchange", "doorlock", "statemachines", "presence"])
@when("Item SchlossWaschkueche_LockState changed")
def door_lock_reported_lock_changes(event):
    """
    send event to DoorLock statemachine if ReportedLock changes
    Args:
        event (_type_): any ReportedLock item
    """
    door_lock_reported_lock_changes.log.info(
        "rule fired because of %s %s --> %s", event.itemName, event.oldItemState, event.itemState)

    DOOR_LOCK_STATE_MACHINE.set_reported_lock(str(event.itemState))
    DOOR_LOCK_STATE_MACHINE.send("tr_reported_lock_change")
    set_mode_item(DOOR_LOCK_STATE_MACHINE.get_name(),
                  DOOR_LOCK_STATE_MACHINE.get_state_name())
