"""Example of python module statemachine: https://pypi.org/project/python-statemachine/"""

import sys
import os
import logging
import inspect


OH_CONF = os.getenv('OPENHAB_CONF')

sys.path.append(OH_CONF + '/habapp/rules/')
from statemachines.hue_offline_statemachine import get_state_machine, HueOfflineStatemachine

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

# https://docs.python.org/3/howto/logging-cookbook.html
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# create formatter and add it to the handlers
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
# add the handlers to the logger
log.addHandler(ch)


def test_state(state_machine, state):
    """make testing of states with logging easier"""
    log.debug("assert: current -> %s / intended -> %s",
              state_machine.current_state.id, state)
    assert state_machine.current_state.id == state


def test_default_state():
    """Test if default (initial) state is OK
    """
    function_name = inspect.currentframe().f_code.co_name
    print("\n########## %s #########", function_name)

    state_machine = HueOfflineStatemachine(
        name="TestMachine", logger=log)

    test_state(state_machine, "st_online_off")


def test_offline_state():
    """Test offline state handling"""
    function_name = inspect.currentframe().f_code.co_name
    print("\n########## %s #########", function_name)

    state_machine = get_state_machine("TestMachine", logger=log)

    state_machine.set_offline(True)
    state_machine.send("tr_online_change")
    test_state(state_machine, "st_offline")

    state_machine.set_offline(False)
    state_machine.send("tr_online_change")
    test_state(state_machine, "st_online_off")

    state_machine.set_state(True)
    state_machine.send("tr_state_change")
    test_state(state_machine, "st_online_on")

    state_machine.set_offline(True)
    state_machine.send("tr_online_change")
    test_state(state_machine, "st_offline")

    state_machine.set_offline(False)
    state_machine.send("tr_online_change")
    test_state(state_machine, "st_online_on")


def test_state_state():
    """Test offline state handling"""
    function_name = inspect.currentframe().f_code.co_name
    print("\n########## %s #########", function_name)

    state_machine = get_state_machine("TestMachine", logger=log)

    state_machine.set_state(True)
    state_machine.send("tr_state_change")
    test_state(state_machine, "st_online_on")

    state_machine.set_state(False)
    state_machine.send("tr_state_change")
    test_state(state_machine, "st_online_off")

    state_machine.set_offline(True)
    state_machine.send("tr_online_change")
    test_state(state_machine, "st_offline")

    state_machine.set_state(True)
    state_machine.send("tr_state_change")
    test_state(state_machine, "st_offline")

    state_machine.set_state(False)
    state_machine.send("tr_state_change")
    test_state(state_machine, "st_offline")


test_default_state()
test_offline_state()
test_state_state()
