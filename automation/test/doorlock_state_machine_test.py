"""Example of python module statemachine: https://pypi.org/project/python-statemachine/"""

import sys
import os
import logging
import inspect


OH_CONF = os.getenv('OPENHAB_CONF')

print("OH_CONF = " + OH_CONF)

sys.path.append(os.path.join(OH_CONF, "automation/lib/python/personal"))
sys.path.append(os.path.join(OH_CONF, "automation/lib/python"))
from door_lock_statemachine import door_lock_statemachine

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

    state_machine = door_lock_statemachine(
        name="TestMachine", logger=log)

    test_state(state_machine, "unlocked")


def test_dark_outside_state():
    """Test if auto, manual and vacation state is OK
    """
    function_name = inspect.currentframe().f_code.co_name
    print(f"\n########## {function_name} #########")

    state_machine = door_lock_statemachine(
        name=function_name, logger=log)

    state_machine.set_dark_outside(True)
    state_machine.send("tr_dark_outside_change")
    test_state(state_machine, "locked")

    state_machine.set_dark_outside(False)
    state_machine.send("tr_dark_outside_change")
    test_state(state_machine, "unlocked")

    # ####################
    # DARK_OUTSIDE == TRUE
    # ####################
    state_machine.set_dark_outside(True)
    state_machine.send("tr_dark_outside_change")
    test_state(state_machine, "locked")

    # check presence
    state_machine.set_presence(False)
    state_machine.send("tr_presence_change")
    test_state(state_machine, "locked")

    state_machine.set_presence(True)
    state_machine.send("tr_presence_change")
    test_state(state_machine, "locked")

    # check light
    state_machine.set_light(True)
    state_machine.send("tr_light_change")
    test_state(state_machine, "unlocked")

    state_machine.set_light(False)
    state_machine.send("tr_light_change")
    test_state(state_machine, "locked")

    # check door state
    state_machine.set_door_open(True)
    state_machine.send("tr_door_state_change")
    test_state(state_machine, "error")

    state_machine.set_door_open(False)
    state_machine.send("tr_door_state_change")
    test_state(state_machine, "locked")

    # #####################
    # DARK_OUTSIDE == FALSE
    # #####################

    state_machine.set_dark_outside(False)
    state_machine.send("tr_dark_outside_change")
    test_state(state_machine, "unlocked")

    # check presence
    state_machine.set_presence(False)
    state_machine.send("tr_presence_change")
    test_state(state_machine, "locked")

    state_machine.set_presence(True)
    state_machine.send("tr_presence_change")
    test_state(state_machine, "unlocked")

    # check light
    state_machine.set_light(True)
    state_machine.send("tr_light_change")
    test_state(state_machine, "unlocked")

    state_machine.set_light(False)
    state_machine.send("tr_light_change")
    test_state(state_machine, "unlocked")

    # check door open
    state_machine.set_door_open(True)
    state_machine.send("tr_door_state_change")
    test_state(state_machine, "unlocked")

    state_machine.set_door_open(False)
    state_machine.send("tr_door_state_change")
    test_state(state_machine, "unlocked")


def test_door_open_state():
    """Test if auto, manual and vacation state is OK
    """
    function_name = inspect.currentframe().f_code.co_name
    print(f"\n########## {function_name} #########")

    state_machine = door_lock_statemachine(
        name=function_name, logger=log)

    state_machine.set_door_open(True)
    state_machine.send("tr_door_state_change")
    test_state(state_machine, "unlocked")

    state_machine.set_door_open(False)
    state_machine.send("tr_door_state_change")
    test_state(state_machine, "unlocked")

    # ################
    # DOOR == OPEN
    # ################
    state_machine.set_door_open(True)
    state_machine.send("tr_door_state_change")
    test_state(state_machine, "unlocked")

    # check presence
    state_machine.set_presence(False)
    state_machine.send("tr_presence_change")
    test_state(state_machine, "error")

    state_machine.set_presence(True)
    state_machine.send("tr_presence_change")
    test_state(state_machine, "unlocked")

    # check light
    state_machine.set_light(True)
    state_machine.send("tr_light_change")
    test_state(state_machine, "unlocked")

    state_machine.set_light(False)
    state_machine.send("tr_light_change")
    test_state(state_machine, "unlocked")

    # check dark_outside
    state_machine.set_dark_outside(True)
    state_machine.send("tr_dark_outside_change")
    test_state(state_machine, "error")

    state_machine.set_dark_outside(False)
    state_machine.send("tr_dark_outside_change")
    test_state(state_machine, "unlocked")

    # ################
    # DOOR == CLOSED
    # ################

    state_machine.set_door_open(False)
    state_machine.send("tr_door_state_change")
    test_state(state_machine, "unlocked")

    # check presence
    state_machine.set_presence(False)
    state_machine.send("tr_presence_change")
    test_state(state_machine, "locked")

    state_machine.set_presence(True)
    state_machine.send("tr_presence_change")
    test_state(state_machine, "unlocked")

    # check light
    state_machine.set_light(True)
    state_machine.send("tr_light_change")
    test_state(state_machine, "unlocked")

    state_machine.set_light(False)
    state_machine.send("tr_light_change")
    test_state(state_machine, "unlocked")

    # check dark_outside
    state_machine.set_dark_outside(True)
    state_machine.send("tr_dark_outside_change")
    test_state(state_machine, "locked")

    state_machine.set_dark_outside(False)
    state_machine.send("tr_dark_outside_change")
    test_state(state_machine, "unlocked")


def test_error_state():
    """Test if auto, manual and vacation state is OK
    """
    function_name = inspect.currentframe().f_code.co_name
    print(f"\n########## {function_name} #########")

    state_machine = door_lock_statemachine(
        name=function_name, logger=log)

    state_machine.set_lock_error(True)
    state_machine.send("tr_error_change")
    test_state(state_machine, "error")

    state_machine.set_lock_error(False)
    state_machine.send("tr_error_change")
    test_state(state_machine, "unlocked")

    state_machine.set_lock_error(True)
    state_machine.send("tr_error_change")
    test_state(state_machine, "error")

    # check presence
    state_machine.set_presence(True)
    state_machine.send("tr_presence_change")
    test_state(state_machine, "error")

    state_machine.set_presence(False)
    state_machine.send("tr_presence_change")
    test_state(state_machine, "error")

    # check door open
    state_machine.set_door_open(True)
    state_machine.send("tr_door_state_change")
    test_state(state_machine, "error")

    state_machine.set_door_open(False)
    state_machine.send("tr_door_state_change")
    test_state(state_machine, "error")

    # check light
    state_machine.set_light(True)
    state_machine.send("tr_light_change")
    test_state(state_machine, "error")

    state_machine.set_light(False)
    state_machine.send("tr_light_change")
    test_state(state_machine, "error")

    # check dark
    state_machine.set_dark_outside(True)
    state_machine.send("tr_dark_outside_change")
    test_state(state_machine, "error")

    state_machine.set_dark_outside(False)
    state_machine.send("tr_dark_outside_change")
    test_state(state_machine, "error")


def test_light_state():
    """Test if auto, manual and vacation state is OK
    """
    function_name = inspect.currentframe().f_code.co_name
    print(f"\n########## {function_name} #########")

    state_machine = door_lock_statemachine(
        name=function_name, logger=log)

    state_machine.set_light(True)
    state_machine.send("tr_light_change")
    test_state(state_machine, "unlocked")

    state_machine.set_light(False)
    state_machine.send("tr_light_change")
    test_state(state_machine, "unlocked")

    # ################
    # LIGHT == ON
    # ################
    state_machine.set_light(True)
    state_machine.send("tr_light_change")
    test_state(state_machine, "unlocked")

    # check presence
    state_machine.set_presence(False)
    state_machine.send("tr_presence_change")
    test_state(state_machine, "locked")

    state_machine.set_presence(True)
    state_machine.send("tr_presence_change")
    test_state(state_machine, "unlocked")

    # check door_open
    state_machine.set_door_open(True)
    state_machine.send("tr_door_state_change")
    test_state(state_machine, "unlocked")

    state_machine.set_door_open(False)
    state_machine.send("tr_door_state_change")
    test_state(state_machine, "unlocked")

    # check dark_outside
    state_machine.set_dark_outside(True)
    state_machine.send("tr_dark_outside_change")
    test_state(state_machine, "unlocked")

    state_machine.set_dark_outside(False)
    state_machine.send("tr_dark_outside_change")
    test_state(state_machine, "unlocked")

    # ################
    # LIGHT == OFF
    # ################
    state_machine.set_light(False)
    state_machine.send("tr_dark_outside_change")
    test_state(state_machine, "unlocked")

    # check presence
    state_machine.set_presence(False)
    state_machine.send("tr_presence_change")
    test_state(state_machine, "locked")

    state_machine.set_presence(True)
    state_machine.send("tr_presence_change")
    test_state(state_machine, "unlocked")

    # check door_open
    state_machine.set_door_open(True)
    state_machine.send("tr_door_state_change")
    test_state(state_machine, "unlocked")

    state_machine.set_door_open(False)
    state_machine.send("tr_door_state_change")
    test_state(state_machine, "unlocked")

    # check dark_outside
    state_machine.set_dark_outside(True)
    state_machine.send("tr_dark_outside_change")
    test_state(state_machine, "locked")

    state_machine.set_dark_outside(False)
    state_machine.send("tr_dark_outside_change")
    test_state(state_machine, "unlocked")


def test_presence_state():
    """Test if auto, manual and vacation state is OK
    """
    function_name = inspect.currentframe().f_code.co_name
    print(f"\n########## {function_name} #########")

    state_machine = door_lock_statemachine(
        name=function_name, logger=log)

    state_machine.set_presence(True)
    state_machine.send("tr_presence_change")
    test_state(state_machine, "unlocked")

    state_machine.set_presence(False)
    state_machine.send("tr_presence_change")
    test_state(state_machine, "locked")

    # ################
    # PRESENCE == TRUE
    # ################
    state_machine.set_presence(True)
    state_machine.send("tr_presence_change")
    test_state(state_machine, "unlocked")

    # check light
    state_machine.set_light(False)
    state_machine.send("tr_light_change")
    test_state(state_machine, "unlocked")

    state_machine.set_light(True)
    state_machine.send("tr_light_change")
    test_state(state_machine, "unlocked")

    # check door_open
    state_machine.set_door_open(True)
    state_machine.send("tr_door_state_change")
    test_state(state_machine, "unlocked")

    state_machine.set_door_open(False)
    state_machine.send("tr_door_state_change")
    test_state(state_machine, "unlocked")

    # check dark_outside
    state_machine.set_dark_outside(True)
    state_machine.send("tr_dark_outside_change")
    test_state(state_machine, "unlocked")

    state_machine.set_dark_outside(False)
    state_machine.send("tr_dark_outside_change")
    test_state(state_machine, "unlocked")

    # #################
    # PRESENCE == FALSE
    # #################
    state_machine.set_presence(False)
    state_machine.send("tr_presence_change")
    test_state(state_machine, "locked")

    # check light
    state_machine.set_light(False)
    state_machine.send("tr_light_change")
    test_state(state_machine, "locked")

    state_machine.set_light(True)
    state_machine.send("tr_light_change")
    test_state(state_machine, "locked")

    # check door_open
    state_machine.set_door_open(True)
    state_machine.send("tr_door_state_change")
    test_state(state_machine, "error")

    state_machine.set_door_open(False)
    state_machine.send("tr_door_state_change")
    test_state(state_machine, "locked")

    # check dark_outside
    state_machine.set_dark_outside(True)
    state_machine.send("tr_dark_outside_change")
    test_state(state_machine, "locked")

    state_machine.set_dark_outside(False)
    state_machine.send("tr_dark_outside_change")
    test_state(state_machine, "locked")


test_default_state()
test_dark_outside_state()
test_door_open_state()
test_error_state()
test_light_state()
test_presence_state()
