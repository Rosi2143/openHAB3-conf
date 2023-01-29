"""Example of python module statemachine: https://pypi.org/project/python-statemachine/"""

import sys
import os
import logging
import inspect


OH_CONF = os.getenv('OPENHAB_CONF')

sys.path.append(os.path.join(OH_CONF, "automation/lib/python/personal"))
sys.path.append(os.path.join(OH_CONF, "automation/lib/python"))
from thermostat_statemachine import get_state_machine, get_state_machine_list

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
    log.debug(f"assert: {state_machine.current_state.id} == {state}")
    assert state_machine.current_state.id == state


def test_single_sm():
    """Test if default (initial) state is OK
    """
    function_name = inspect.currentframe().f_code.co_name
    print(f"\n########## {function_name} #########")

    state_machine = get_state_machine("TestMachine", logger=log)

    test_state(state_machine, "st_auto")


def test_multiple_sm():
    """Test if default (initial) state is OK
    """
    function_name = inspect.currentframe().f_code.co_name
    print(f"\n########## {function_name} #########")

    for sm_name in ["Test1", "Test-2", "Test--3", "Test--3", "Test-2", "Test1"]:
        print("########################")
        print(f"test statemachine {sm_name}")
        print("########################")

        state_machine = get_state_machine(sm_name, logger=log)

        state_machine.set_mode(state_machine.MANUAL)
        state_machine.send("tr_mode_change")
        test_state(state_machine, "st_manual")

        state_machine.set_mode(state_machine.VACATION)
        state_machine.send("tr_mode_change")
        test_state(state_machine, "st_vacation")


test_single_sm()
test_multiple_sm()
