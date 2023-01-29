"""Example of python module statemachine: https://pypi.org/project/python-statemachine/"""

import sys
import os
import logging
import inspect


OH_CONF = os.getenv('OPENHAB_CONF')

sys.path.append(os.path.join(OH_CONF, "automation/lib/python/personal"))
sys.path.append(os.path.join(OH_CONF, "automation/lib/python"))
from ThermostatStateMachine import ThermostatStateMachine

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

# https://docs.python.org/3/howto/logging-cookbook.html
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
# create formatter and add it to the handlers
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
# add the handlers to the logger
log.addHandler(ch)


def test_state(state_machine, state):
    """make testing of states with logging easier"""
    log.debug(
        f"assert: {state_machine.get_name()} {state_machine.current_state.name} == {state}")
    assert state_machine.current_state.name == state


def test_default_state():
    """Test if default (initial) state is OK
    """
    function_name = inspect.currentframe().f_code.co_name
    print(f"\n########## {function_name} #########")

    state_machine = ThermostatStateMachine(
        name="TestMachine", logger=log)

    test_state(state_machine, "auto")


def test_auto_manual_vacation_state():
    """Test if auto, manual and vacation state is OK
    """
    function_name = inspect.currentframe().f_code.co_name
    print(f"\n########## {function_name} #########")

    state_machine = ThermostatStateMachine(
        name=function_name, logger=log)

    state_machine.set_mode(state_machine.MANUAL)
    state_machine.send("tr_mode_change")
    test_state(state_machine, "manual")

    state_machine.set_mode(state_machine.AUTO)
    state_machine.send("tr_mode_change")
    test_state(state_machine, "auto")

    state_machine.set_mode(state_machine.VACATION)
    state_machine.send("tr_mode_change")
    test_state(state_machine, "vacation")

    state_machine.set_mode(state_machine.AUTO)
    state_machine.send("tr_mode_change")
    test_state(state_machine, "auto")

    state_machine.set_mode(state_machine.VACATION)
    state_machine.send("tr_mode_change")
    test_state(state_machine, "vacation")

    state_machine.set_mode(state_machine.MANUAL)
    state_machine.send("tr_mode_change")
    test_state(state_machine, "manual")


def test_config_change():
    """Test config state change transitions
    """
    function_name = inspect.currentframe().f_code.co_name
    print(f"\n########## {function_name} #########")

    state_machine = ThermostatStateMachine(
        name=function_name, logger=log)

    state_machine.set_config(True)
    state_machine.send("tr_config_change")
    test_state(state_machine, "config")

    state_machine.set_boost(True)
    state_machine.send("tr_boost_change")
    test_state(state_machine, "config")

    state_machine.set_window_open(True)
    state_machine.send("tr_boost_change")
    test_state(state_machine, "config")

    state_machine.set_mode(state_machine.VACATION)
    state_machine.send("tr_mode_change")
    test_state(state_machine, "config")

    state_machine.set_window_open(False)
    state_machine.send("tr_boost_change")
    test_state(state_machine, "config")

    state_machine.set_mode(state_machine.MANUAL)
    state_machine.send("tr_mode_change")
    test_state(state_machine, "config")

    state_machine.set_boost(False)
    state_machine.send("tr_boost_change")
    test_state(state_machine, "config")

    state_machine.set_config(False)
    state_machine.send("tr_config_change")
    test_state(state_machine, "manual")


def test_window_change():
    """Test window state change transitions
    """
    function_name = inspect.currentframe().f_code.co_name
    print(f"\n########## {function_name} #########")

    state_machine = ThermostatStateMachine(
        name=function_name, logger=log)

    state_machine.set_window_open(True)
    state_machine.send("tr_window_change")
    test_state(state_machine, "off")

    state_machine.set_boost(True)
    state_machine.send("tr_boost_change")
    test_state(state_machine, "off")

    state_machine.set_mode(state_machine.VACATION)
    state_machine.send("tr_mode_change")
    test_state(state_machine, "off")

    state_machine.set_mode(state_machine.MANUAL)
    state_machine.send("tr_mode_change")
    test_state(state_machine, "off")

    state_machine.set_config(True)
    state_machine.send("tr_config_change")
    test_state(state_machine, "config")

    state_machine.set_config(False)
    state_machine.send("tr_config_change")
    test_state(state_machine, "off")

    state_machine.set_boost(False)
    state_machine.send("tr_boost_change")
    test_state(state_machine, "off")

    state_machine.set_window_open(False)
    state_machine.send("tr_window_change")
    test_state(state_machine, "manual")


test_default_state()
test_auto_manual_vacation_state()
test_config_change()
test_window_change()
