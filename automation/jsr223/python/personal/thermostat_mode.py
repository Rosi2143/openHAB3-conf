"""Example of python module statemachine: https://pypi.org/project/python-statemachine/"""

# log:set INFO jsr223.jython.thermostate_mode
# minimum version python-statemachine = 1.0.3

import sys
import os

from core.log import logging, LOG_PREFIX
from core.rules import rule
from core.triggers import when
from core.items import add_item

OH_CONF = os.getenv('OPENHAB_CONF')

sys.path.append(os.path.join(OH_CONF, "automation/lib/python/personal"))
from ThermostatStateMachine import get_state_machine, get_state_machine_list, get_internal_state_machine_state

log = logging.getLogger("{}.thermostate_mode".format(LOG_PREFIX))


def set_mode_item(sm, state):
    mode_item_name = sm + "_Mode"
    mode_item = itemRegistry.getItems(mode_item_name)
    if mode_item == []:
        log.info("ModeItem: " + mode_item_name + " does not exist")
    else:
        events.sendCommand(mode_item_name, state)


@rule("Thermostat_statemachines_create",
      description="initialize the statemachines for thermostats",
      tags=["systemstart", "thermostats", "statemachines"])
@when("System started")
def initialize_thermostate_statemachines(event):
    """setup all statemachines for thermostats"""

    for oh_item in itemRegistry.getItems():

        if "Heizung" in oh_item.getName():

            initialize_thermostate_statemachines.log.debug(
                "handling item: " + oh_item.getName())

            state_machine = get_state_machine(
                oh_item.getName(), initialize_thermostate_statemachines.log)
            item_state = oh_item.getState()

            if unicode(item_state, errors='ignore') == "NULL":
                initialize_thermostate_statemachines.log.debug(
                    "skip handling item: " + oh_item.getName() + " state is NULL")
                continue

            if "BoostMode" in oh_item.getName():
                initialize_thermostate_statemachines.log.info(
                    "handling BoostMode: " + oh_item.getName() + "(" + str(item_state) + ")")
                state_machine.set_boost(oh_item.getState() == "ON")
                state_machine.send("tr_boost_change")
            if "ConfigPending" in oh_item.getName():
                initialize_thermostate_statemachines.log.info(
                    "handling ConfigPending: " + oh_item.getName() + "(" + str(item_state) + ")")
                state_machine.set_config(oh_item.getState() == "ON")
                state_machine.send("tr_config_change")
            if "PartyMode" in oh_item.getName():
                initialize_thermostate_statemachines.log.info(
                    "handling PartyMode: " + oh_item.getName() + "(" + str(item_state) + ")")
                state_machine.set_boost(oh_item.getState() == "ON")
                state_machine.send("tr_party_change")
            if "SetPointMode" in oh_item.getName():
                new_mode = state_machine.state_map[str(
                    int(float(str(item_state))))]
                initialize_thermostate_statemachines.log.info(
                    "handling SetPointMode: " + oh_item.getName() + "(" + new_mode + ")")
                state_machine.set_mode(new_mode)
                state_machine.send("tr_mode_change")
            if "WindowState" in oh_item.getName():
                initialize_thermostate_statemachines.log.info(
                    "handling WindowState: " + oh_item.getName() + "(" + str(item_state) + ")")
                state_machine.set_boost(oh_item.getState() == "ON")
                state_machine.send("tr_window_change")

    for therm_sm in get_state_machine_list().values():
        initialize_thermostate_statemachines.log.info(
            "StateMachine " + therm_sm.get_name() + "(" + str(id(therm_sm)) +
            "): is in state " + therm_sm.get_state_name())
        initialize_thermostate_statemachines.log.debug(
            get_internal_state_machine_state(therm_sm)
        )
        set_mode_item(therm_sm.get_name(), therm_sm.get_state_name())
    initialize_thermostate_statemachines.log.info("Done")

# ####################
# Rules
# ####################

# Check BoostModes


@rule("Thermostat_BoostMode_check",
      description="react on changes in BoostMode",
      tags=["memberchange", "thermostats", "statemachines", "boostmode"])
@when("Member of gThermostate_BoostMode changed")
def thermostate_boost_mode_changes(event):
    """
    send event to Thermostat statemachine if BoostMode changes
    Args:
        event (_type_): any BoostMode item
    """
    thermostate_boost_mode_changes.log.info(
        "rule fired because of %s %s --> %s", event.itemName, event.oldItemState, event.itemState)

    therm_sm = get_state_machine(
        event.itemName, thermostate_boost_mode_changes.log)
    therm_sm.set_boost(str(event.itemState) == "ON")
    therm_sm.send("tr_boost_change")

# Check ConfigModes


@rule("Thermostat_ConfigMode_check",
      description="react on changes in ConfigMode",
      tags=["memberchange", "thermostats", "statemachines", "configmode"])
@when("Member of gThermostate_ConfigsPending changed")
def thermostate_config_mode_changes(event):
    """
    send event to Thermostat statemachine if ConfigMode changes
    Args:
        event (_type_): any ConfigMode item
    """
    thermostate_config_mode_changes.log.info(
        "rule fired because of %s %s --> %s", event.itemName, event.oldItemState, event.itemState)

    therm_sm = get_state_machine(
        event.itemName, thermostate_config_mode_changes.log)
    therm_sm.set_config(str(event.itemState) == "ON")
    therm_sm.send("tr_config_change")

# Check Modes


@rule("Thermostat_Mode_check",
      description="react on changes in Mode",
      tags=["memberchange", "thermostats", "statemachines", "mode"])
@when("Member of gThermostate_SetPointModes changed")
def thermostate_mode_changes(event):
    """
    send event to Thermostat statemachine if Mode changes
    Args:
        event (_type_): any Mode item
    """
    thermostate_mode_changes.log.info(
        "rule fired because of %s %s --> %s", event.itemName, event.oldItemState, event.itemState)

    therm_sm = get_state_machine(event.itemName, thermostate_mode_changes.log)
    thermostate_mode_changes.log.info(therm_sm.get_name())
    if str(event.itemState) in therm_sm.state_map:
        therm_sm.set_mode(therm_sm.state_map[str(event.itemState)])
    else:
        thermostate_mode_changes.log.info(
            "unknown mode %s value for %s", event.itemState, event.itemName)
    thermostate_mode_changes.log.info(therm_sm.get_name())
    therm_sm.send("tr_mode_change")
    thermostate_mode_changes.log.info(therm_sm.get_name())

# Check PartyModes


@rule("Thermostat_PartyMode_check",
      description="react on changes in PartyMode",
      tags=["memberchange", "thermostats", "statemachines", "partymode"])
@when("Member of gThermostate_PartyModes changed")
def thermostate_party_mode_changes(event):
    """
    send event to Thermostat statemachine if PartyMode changes
    Args:
        event (_type_): any PartyMode item
    """
    thermostate_party_mode_changes.log.info(
        "rule fired because of %s %s --> %s", event.itemName, event.oldItemState, event.itemState)

    therm_sm = get_state_machine(
        event.itemName, thermostate_party_mode_changes.log)
    therm_sm.set_party(str(event.itemState) == "ON")
    therm_sm.send("tr_party_change")

# Check WindowStates


@rule("Thermostat_WindowState_check",
      description="react on changes in WindowState",
      tags=["memberchange", "thermostats", "statemachines", "windowmode"])
@when("Member of gThermostate_WindowStates changed")
def thermostate_window_mode_changes(event):
    """
    send event to Thermostat statemachine if WindowState changes
    Args:
        event (_type_): any WindowState item
    """
    thermostate_window_mode_changes.log.info(
        "rule fired because of %s %s --> %s", event.itemName, event.oldItemState, event.itemState)

    therm_sm = get_state_machine(
        event.itemName, thermostate_window_mode_changes.log)
    therm_sm.set_window_open(str(event.itemState) == "ON")
    therm_sm.send("tr_window_change")
