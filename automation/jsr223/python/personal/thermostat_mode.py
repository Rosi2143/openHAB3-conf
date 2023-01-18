"""Example of python module statemachine: https://pypi.org/project/python-statemachine/"""

# log:set INFO jsr223.jython.thermostat_mode

import sys
import os

from core.log import logging, LOG_PREFIX
from core.rules import rule
from core.triggers import when
from core.actions import Ephemeris
from core.items import add_item

OH_CONF = os.getenv('OPENHAB_CONF')

sys.path.append(os.path.join(OH_CONF, "automation/lib/python/personal"))
from ThermostatStateMachine import ThermostatStateMachine
sys.path.append("/home/openhabian/git/python-statemachine")
from statemachine.contrib.diagram import DotGraphMachine
from tests.examples.order_control_machine import OrderControl

scriptpath = os.path.join(OH_CONF, "automation/jsr223/python/personal")
thermostat_list = {}

log = logging.getLogger("{}.thermostat_mode".format(LOG_PREFIX))


def get_state_machine(item_name):
    """make sure a statemachine exists for the item
    Args:
        item_name (string): name of the item <thing_name>_<itempart>
    Returns:
        new or existing statemachine
    """
    thing_name = item_name.split("_")[0]
    if thing_name not in thermostat_list:
        thermostat_list[thing_name] = ThermostatStateMachine(thing_name, log)
        log.info("Created ThermostatSm: " +
                 thermostat_list[thing_name].get_name())

        # also accepts instances
        graph = DotGraphMachine(thermostat_list[thing_name])
        graph().write_png(os.path.join(scriptpath, "images",
                                       thermostat_list[thing_name].get_name() + "_thermostat_sm.png"))

    return thermostat_list[thing_name]


@rule("Thermostat_statemachines_create",
      description="initialize the statemachines for thermostats",
      tags=["systemstart", "thermostats", "statemachines"])
@when("System started")
def initialize_thermostat_statemachines(event):
    """setup all statemachines for thermostats"""

    for oh_item in itemRegistry.getItems():

        if "Heizung" in oh_item.getName():

            state_machine = get_state_machine(oh_item.getName())
            item_state = oh_item.getState()

            if "BoostMode" in oh_item.getName():
                initialize_thermostat_statemachines.log.info(
                    "handling: BoostMode: " + oh_item.getName() + "(" + str(item_state) + ")")
                state_machine.set_boost(oh_item.getState() == "ON")
                state_machine.send("tr_boost_change")
            if "ConfigPending" in oh_item.getName():
                initialize_thermostat_statemachines.log.info(
                    "handling: ConfigPending: " + oh_item.getName() + "(" + str(item_state) + ")")
                state_machine.set_config(oh_item.getState() == "ON")
                state_machine.send("tr_config_change")
            if "PartyMode" in oh_item.getName():
                initialize_thermostat_statemachines.log.info(
                    "handling: PartyMode" + oh_item.getName() + "(" + str(item_state) + ")")
                state_machine.set_boost(oh_item.getState() == "ON")
                state_machine.send("tr_party_change")
            if "SetPointMode" in oh_item.getName():
                initialize_thermostat_statemachines.log.info(
                    "handling: SetPointMode" + oh_item.getName() + "(" + str(item_state) + ")")
                state_machine.set_boost(int(item_state))
                if int(item_state) == 0:
                    state_machine.send("tr_mode_change")
                elif int(item_state) == 1:
                    state_machine.send("tr_mode_change")
                else:
                    state_machine.send("tr_mode_change")
            if "WindowState" in oh_item.getName():
                initialize_thermostat_statemachines.log.info(
                    "handling: WindowState" + oh_item.getName() + "(" + str(item_state) + ")")
                state_machine.set_boost(oh_item.getState() == "ON")
                state_machine.send("tr_window_change")
