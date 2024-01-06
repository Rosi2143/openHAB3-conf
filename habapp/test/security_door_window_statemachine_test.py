"""Example of python module statemachine: https://pypi.org/project/python-statemachine/"""

import sys
import os
import logging
import inspect


OH_CONF = os.getenv("OPENHAB_CONF")

print("OH_CONF = " + OH_CONF)

sys.path.append(OH_CONF + "/habapp/rules/")
from statemachines.SecurityDoorWindowStatemachine import SecurityDoorWindowStatemachine

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

# https://docs.python.org/3/howto/logging-cookbook.html
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
# create formatter and add it to the handlers
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
# add the handlers to the logger
log.addHandler(ch)


def test_state(state_machine, state):
    """make testing of states with logging easier"""
    log.info(
        "assert: %s [current]%s == [expect]%s",
        state_machine.get_name(),
        state_machine.current_state.name,
        state,
    )
    assert state_machine.current_state.name == state


def run_tests(event, test_set, state_machine):
    """run all tests in the test_set
       This is the central test function

    Args:
        event (string): event that shall be tested
        test_set (_type_): map of events and states that are tested
        state_machine (statemachine): statemachine that is tested
    """

    event_function = getattr(state_machine, "set_" + event)
    for test, results in test_set.items():
        log.info("%s: ********** testing '%s' *************", event, test)
        test_function = getattr(state_machine, "set_" + test)

        log.debug("%s: ********** testing '%s'->True *************", event, test)
        test_function(True)
        state_machine.send("tr_" + test)
        test_state(state_machine, results["ON"])

        log.debug("%s: ********** testing '%s'->False *************", event, event)
        event_function(False)
        state_machine.send("tr_" + event)
        test_state(state_machine, results["ON_OFF"])

        log.debug("%s: ********** testing '%s'->True *************", event, event)
        event_function(True)
        state_machine.send("tr_" + event)
        test_state(state_machine, results["ON_ON"])

        log.debug("%s: ********** testing '%s'->False *************", event, test)
        test_function(False)
        state_machine.send("tr_" + test)
        test_state(state_machine, results["OFF"])


def test_default_state():
    """Test if default (initial) state is OK"""
    function_name = inspect.currentframe().f_code.co_name
    print("\n########## %s #########", function_name)

    state_machine = SecurityDoorWindowStatemachine(name="TestMachine", logger=log)

    test_state(state_machine, "black")


def test_bell_rang_state():
    """Test if bell_rang state is OK"""
    function_name = inspect.currentframe().f_code.co_name
    print("\n########## %s #########", function_name)

    state_machine = SecurityDoorWindowStatemachine(name=function_name, logger=log)

    # bell_rang is active
    state_machine.set_bell_rang(True)
    state_machine.send("tr_bell_rang")
    test_state(state_machine, "yellow")

    test_set = {
        "lock_error": {"ON": "red", "ON_OFF": "red", "ON_ON": "red", "OFF": "yellow"},
        "outer_door_open": {
            "ON": "yellow",
            "ON_OFF": "purple",
            "ON_ON": "yellow",
            "OFF": "yellow",
        },
        "window_open": {
            "ON": "yellow",
            "ON_OFF": "blue",
            "ON_ON": "yellow",
            "OFF": "yellow",
        },
        "timeout_state": {
            "ON": "green",
            "ON_OFF": "green",
            "ON_ON": "yellow",
            "OFF": "green",
        },
    }

    run_tests("bell_rang", test_set, state_machine)


def test_lock_error_state():
    """Test if lock_error state is OK"""
    function_name = inspect.currentframe().f_code.co_name
    print("\n########## %s #########", function_name)

    state_machine = SecurityDoorWindowStatemachine(name=function_name, logger=log)

    # bell_rang is active
    state_machine.set_lock_error(True)
    state_machine.send("tr_lock_error")
    test_state(state_machine, "red")

    test_set = {
        "bell_rang": {"ON": "red", "ON_OFF": "yellow", "ON_ON": "red", "OFF": "red"},
        "outer_door_open": {
            "ON": "red",
            "ON_OFF": "purple",
            "ON_ON": "red",
            "OFF": "red",
        },
        "window_open": {"ON": "red", "ON_OFF": "blue", "ON_ON": "red", "OFF": "red"},
        "timeout_state": {"ON": "red", "ON_OFF": "green", "ON_ON": "red", "OFF": "red"},
    }

    run_tests("lock_error", test_set, state_machine)


def test_outer_door_state():
    """Test if outer_door_open state is OK"""
    function_name = inspect.currentframe().f_code.co_name
    print("\n########## %s #########", function_name)

    state_machine = SecurityDoorWindowStatemachine(name=function_name, logger=log)

    # outer_door_open is active
    state_machine.set_outer_door_open(True)
    state_machine.send("tr_outer_door_open")
    test_state(state_machine, "purple")

    test_set = {
        "bell_rang": {
            "ON": "yellow",
            "ON_OFF": "yellow",
            "ON_ON": "yellow",
            "OFF": "purple",
        },
        "lock_error": {"ON": "red", "ON_OFF": "red", "ON_ON": "red", "OFF": "purple"},
        "window_open": {
            "ON": "purple",
            "ON_OFF": "blue",
            "ON_ON": "purple",
            "OFF": "purple",
        },
        "timeout_state": {
            "ON": "purple",
            "ON_OFF": "green",
            "ON_ON": "purple",
            "OFF": "purple",
        },
    }

    run_tests("outer_door_open", test_set, state_machine)


def test_window_state():
    """Test if window_open state is OK"""
    function_name = inspect.currentframe().f_code.co_name
    print("\n########## %s #########", function_name)

    state_machine = SecurityDoorWindowStatemachine(name=function_name, logger=log)

    # window_open is active
    state_machine.set_window_open(True)
    state_machine.send("tr_window_open")
    test_state(state_machine, "blue")

    test_set = {
        "bell_rang": {
            "ON": "yellow",
            "ON_OFF": "yellow",
            "ON_ON": "yellow",
            "OFF": "blue",
        },
        "lock_error": {"ON": "red", "ON_OFF": "red", "ON_ON": "red", "OFF": "blue"},
        "outer_door_open": {
            "ON": "purple",
            "ON_OFF": "purple",
            "ON_ON": "purple",
            "OFF": "blue",
        },
        "timeout_state": {
            "ON": "black",
            "ON_OFF": "black",
            "ON_ON": "blue",
            "OFF": "black",
        },
    }

    run_tests("window_open", test_set, state_machine)


def test_timeout_state():
    """Test if timeout_open state is OK"""
    function_name = inspect.currentframe().f_code.co_name
    print("\n########## %s #########", function_name)

    state_machine = SecurityDoorWindowStatemachine(name=function_name, logger=log)

    # timeout_open is active
    state_machine.set_timeout_state(True)
    state_machine.send("tr_timeout_state")
    test_state(state_machine, "black")

    test_set = {
        "bell_rang": {
            "ON": "yellow",
            "ON_OFF": "green",
            "ON_ON": "black",
            "OFF": "black",
        },
        "lock_error": {"ON": "red", "ON_OFF": "red", "ON_ON": "red", "OFF": "green"},
        "outer_door_open": {
            "ON": "purple",
            "ON_OFF": "purple",
            "ON_ON": "purple",
            "OFF": "green",
        },
        "window_open": {
            "ON": "blue",
            "ON_OFF": "black",
            "ON_ON": "black",
            "OFF": "black",
        },
    }

    run_tests("timeout_state", test_set, state_machine)


def test_light_level():
    """Test if light level is correctly set"""
    function_name = inspect.currentframe().f_code.co_name
    print("\n########## %s #########", function_name)

    state_machine = SecurityDoorWindowStatemachine(name=function_name, logger=log)

    assert state_machine.get_light_level() == 0

    state_machine.set_bell_rang(True)
    state_machine.send("tr_bell_rang")
    assert state_machine.get_light_level() != 0

    state_machine.set_bell_rang(False)
    state_machine.send("tr_bell_rang")
    assert state_machine.get_light_level() != 0
    state_machine.send("tr_timeout_state")
    assert state_machine.get_light_level() == 0


def test_timeout_second():
    """Test if timeout value is correctly set"""
    function_name = inspect.currentframe().f_code.co_name
    print("\n########## %s #########", function_name)

    state_machine = SecurityDoorWindowStatemachine(name=function_name, logger=log)

    # black == 0
    test_state(state_machine, "black")
    assert state_machine.get_timeout_sec() == 0

    # blue == 10
    state_machine.set_window_open(True)
    state_machine.send("tr_window_open")
    test_state(state_machine, "blue")
    assert state_machine.get_timeout_sec() == 20

    # green == 20
    state_machine.set_window_open(False)
    state_machine.send("tr_window_open")
    test_state(state_machine, "green")
    assert state_machine.get_timeout_sec() == 10

    # purple == 0
    state_machine.set_outer_door_open(True)
    state_machine.send("tr_outer_door_open")
    test_state(state_machine, "purple")
    assert state_machine.get_timeout_sec() == 0

    # red == 0
    state_machine.set_lock_error(True)
    state_machine.send("tr_lock_error")
    test_state(state_machine, "red")
    assert state_machine.get_timeout_sec() == 0

    # yellow == 20
    state_machine.set_lock_error(False)
    state_machine.send("tr_lock_error")
    state_machine.set_bell_rang(True)
    state_machine.send("tr_bell_rang")
    test_state(state_machine, "yellow")
    assert state_machine.get_timeout_sec() == 0


test_default_state()
test_bell_rang_state()
test_lock_error_state()
test_outer_door_state()
test_window_state()
test_timeout_state()
test_light_level()
test_timeout_second()
