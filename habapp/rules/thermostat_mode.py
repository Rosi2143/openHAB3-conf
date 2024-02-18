"""Example of python module statemachine: https://pypi.org/project/python-statemachine/"""

# log:set INFO jsr223.jython.thermostate_mode
# minimum version python-statemachine = 1.0.3

import logging  # required for extended logging

import os
import sys
import HABApp
from HABApp.core.events import ValueChangeEvent, ValueChangeEventFilter
from HABApp.openhab.items import StringItem, OpenhabItem

log = logging.getLogger("ThermostatMode")

param_file = "openhab"
# read the low bat threshold from the parameter file
OH_CONF = HABApp.DictParameter(param_file, "OH_Directories", default_value="")[
    "OPENHAB_CONF"
]
HABAPP_RULES = HABApp.DictParameter(param_file, "HABAPP_Directories", default_value="")[
    "HABAPP_RULES"
]

sys.path.append(os.path.join(OH_CONF, HABAPP_RULES))

from statemachines.ThermostatStatemachine import (
    get_state_machine,
    get_state_machine_list,
    get_internal_state_machine_state,
)


class ThermostatStatemachineRule(HABApp.Rule):
    """statemachine class"""

    def __init__(self):
        """setup all statemachines for thermostats"""
        super().__init__()

        for oh_item in self.get_items(OpenhabItem):

            item_name = oh_item.name
            if oh_item.get_value() is None:
                item_state = 0
            else:
                item_state = str(oh_item.get_value())

            if "Heizung" in item_name:

                log.debug("handling item: %s", item_name)

                state_machine = get_state_machine(item_name, log)

                if item_state is None:
                    log.debug("skip handling item: %s state is None", item_name)
                    continue

                if "BoostMode" in item_name:
                    log.info("handling BoostMode: %s (%s)", item_name, item_state)
                    state_machine.set_boost(oh_item.get_value() == "ON")
                    state_machine.send("tr_boost_change")
                    oh_item.listen_event(
                        self.boost_mode_change, ValueChangeEventFilter()
                    )
                if "ConfigPending" in item_name:
                    log.info("handling ConfigPending: %s (%s)", item_name, item_state)
                    state_machine.set_config(oh_item.get_value() == "ON")
                    state_machine.send("tr_config_change")
                    oh_item.listen_event(
                        self.config_mode_change, ValueChangeEventFilter()
                    )
                if "SetPointMode" in item_name:
                    new_mode = state_machine.state_map[str(int(float(item_state)))]
                    log.info("handling SetPointMode: %s (%s)", item_name, new_mode)
                    state_machine.set_mode(new_mode)
                    state_machine.send("tr_mode_change")
                    oh_item.listen_event(
                        self.setpoint_mode_change, ValueChangeEventFilter()
                    )
                if "PartyMode" in item_name:
                    log.info("handling PartyMode: %s (%s)", item_name, item_state)
                    state_machine.set_boost(oh_item.get_value() == "ON")
                    state_machine.send("tr_party_change")
                    oh_item.listen_event(
                        self.party_mode_change, ValueChangeEventFilter()
                    )
                if "WindowState" in item_name:
                    log.info("handling WindowState: %s (%s)", item_name, item_state)
                    state_machine.set_boost(oh_item.get_value() == "ON")
                    state_machine.send("tr_window_change")
                    oh_item.listen_event(
                        self.window_state_change, ValueChangeEventFilter()
                    )

        for therm_sm in get_state_machine_list().values():
            log.info(
                "StateMachine %s(%s): is in state %s",
                therm_sm.get_name(),
                str(id(therm_sm)),
                therm_sm.get_state_name(),
            )
            log.debug(get_internal_state_machine_state(therm_sm))
            self.set_mode_item(therm_sm.get_name(), therm_sm.get_state_name())
        log.info("Done")

    def set_mode_item(self, state_machine, state):
        """set the state of a mode item"""
        mode_item_name = state_machine + "_Mode"
        if self.openhab.item_exists(mode_item_name):
            mode_item = StringItem.get_item(mode_item_name)
            mode_item.oh_send_command(state)
        else:
            log.info("ModeItem: %s does not exist", mode_item_name)

    # ####################
    # Rules
    # ####################

    # Check BoostModes
    def boost_mode_change(self, event: ValueChangeEvent):
        """
        send event to Thermostat statemachine if BoostMode changes
        Args:
            event (_type_): any BoostMode item
        """
        log.info(
            "rule fired because of %s %s --> %s",
            event.name,
            event.old_value,
            event.value,
        )

        therm_sm = get_state_machine(event.name, log)
        therm_sm.set_boost(str(event.value) == "ON")
        therm_sm.send("tr_boost_change")
        self.set_mode_item(therm_sm.get_name(), therm_sm.get_state_name())

    # Check ConfigModes
    def config_mode_change(self, event: ValueChangeEvent):
        """
        send event to Thermostat statemachine if ConfigMode changes
        Args:
            event (_type_): any ConfigMode item
        """
        log.info(
            "rule fired because of %s %s --> %s",
            event.name,
            event.old_value,
            event.value,
        )

        therm_sm = get_state_machine(event.name, log)
        therm_sm.set_config(str(event.value) == "ON")
        therm_sm.send("tr_config_change")
        self.set_mode_item(therm_sm.get_name(), therm_sm.get_state_name())

    # Check SetPointModes
    def setpoint_mode_change(self, event: ValueChangeEvent):
        """
        send event to Thermostat statemachine if Mode changes
        Args:
            event (_type_): any SetPointMode item
        """
        log.info(
            "rule fired because of %s %s --> %s",
            event.name,
            event.old_value,
            event.value,
        )

        therm_sm = get_state_machine(event.name, log)
        log.info(therm_sm.get_name())
        if str(event.value) in therm_sm.state_map:
            therm_sm.set_mode(therm_sm.state_map[str(event.value)])
        else:
            log.info("unknown mode %s value for %s", event.value, event.name)
        therm_sm.send("tr_mode_change")
        self.set_mode_item(therm_sm.get_name(), therm_sm.get_state_name())

    # Check PartyModes
    def party_mode_change(self, event: ValueChangeEvent):
        """
        send event to Thermostat statemachine if PartyMode changes
        Args:
            event (_type_): any PartyMode item
        """
        log.info(
            "rule fired because of %s %s --> %s",
            event.name,
            event.old_value,
            event.value,
        )

        therm_sm = get_state_machine(event.name, log)
        therm_sm.set_party(str(event.value) == "ON")
        therm_sm.send("tr_party_change")
        self.set_mode_item(therm_sm.get_name(), therm_sm.get_state_name())

    # Check WindowStates
    def window_state_change(self, event: ValueChangeEvent):
        """
        send event to Thermostat statemachine if WindowState changes
        Args:
            event (_type_): any WindowState item
        """
        log.info(
            "rule fired because of %s %s --> %s",
            event.name,
            event.old_value,
            event.value,
        )

        therm_sm = get_state_machine(event.name, log)
        therm_sm.set_window_open(str(event.value) == "ON")
        therm_sm.send("tr_window_change")
        self.set_mode_item(therm_sm.get_name(), therm_sm.get_state_name())


# Rules
ThermostatStatemachineRule()
