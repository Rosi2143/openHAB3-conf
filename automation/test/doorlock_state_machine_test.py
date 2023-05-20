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
    log.debug(
        "assert: %s [current]%s == [expect]%s",
        state_machine.get_name(),
        state_machine.current_state.name,
        state)
    assert state_machine.current_state.name == state

    # simulate the lock is reporting back the correct result
    if state == "locked":
        state_machine.set_reported_lock(state_machine.LOCKED)
    else:
        state_machine.set_reported_lock(state_machine.UNLOCKED)


def run_tests(event, base_test, test_set, state_machine):

    event_function = getattr(state_machine, "set_" + event)

    event_function(True)
    state_machine.send("tr_" + event + "_change")
    test_state(state_machine, base_test[0])

    event_function(False)
    state_machine.send("tr_" + event + "_change")
    test_state(state_machine, base_test[1])

    # ####################
    # DARK_OUTSIDE == TRUE
    # ####################

    event_function(True)
    state_machine.send("tr_" + event + "_change")
    test_state(state_machine, base_test[0])

    for test, results in test_set.items():
        log.info("")
        log.info("")
        log.info("*************************************")
        log.info("%s: ********** testing '%s' *************", event, test)
        log.info("*************************************")
        test_function = getattr(state_machine, "set_" + test)

        log.debug("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        log.debug(
            "%s: ********** testing '%s'->True:[ON] *************", event, test)
        test_function(True)
        state_machine.send("tr_" + test + "_change")
        test_state(state_machine, results["ON"])

        log.debug("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        log.debug(
            "%s: ********** testing '%s'->False:[ON_OFF] *************", event, event)
        event_function(False)
        state_machine.send("tr_" + event + "_change")
        test_state(state_machine, results["ON_OFF"])

        log.debug("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        log.debug(
            "%s: ********** testing '%s'->True:[ON_ON] *************", event, event)
        event_function(True)
        state_machine.send("tr_" + event + "_change")
        test_state(state_machine, results["ON_ON"])

        log.debug("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
        log.debug(
            "%s: ********** testing '%s'->False:[OFF] *************", event, test)
        test_function(False)
        state_machine.send("tr_" + test + "_change")
        test_state(state_machine, results["OFF"])


def test_default_state():
    """Test if default (initial) state is OK
    """
    function_name = inspect.currentframe().f_code.co_name
    print("\n########## %s #########", function_name)

    state_machine = door_lock_statemachine(
        name="TestMachine", logger=log)

    test_state(state_machine, "unlocked")


def test_dark_outside_state():
    """Test if dark outside state is OK"""
    function_name = inspect.currentframe().f_code.co_name
    print("\n########## %s #########", function_name)

    state_machine = door_lock_statemachine(
        name=function_name, logger=log)

    test_set = {"door_open": {"ON": "error",
                              "ON_OFF": "unlocked",
                              "ON_ON": "error",
                              "OFF": "locked"
                              },
                "light": {"ON": "unlocked",
                          "ON_OFF": "unlocked",
                          "ON_ON": "unlocked",
                          "OFF": "locked"
                          },
                "presence": {"ON": "locked",
                             "ON_OFF": "locked",
                             "ON_ON": "locked",
                             "OFF": "locked"
                             }
                }

    run_tests("dark_outside", ["locked", "locked"], test_set, state_machine)


def test_door_open_state():
    """Test if door open state is OK"""
    function_name = inspect.currentframe().f_code.co_name
    print("\n########## %s #########", function_name)

    state_machine = door_lock_statemachine(
        name=function_name, logger=log)

    test_set = {"dark_outside": {"ON": "error",
                                 "ON_OFF": "locked",
                                 "ON_ON": "error",
                                 "OFF": "unlocked"
                                 },
                "light": {"ON": "unlocked",
                          "ON_OFF": "unlocked",
                          "ON_ON": "unlocked",
                          "OFF": "unlocked"
                          },
                "presence": {"ON": "unlocked",
                             "ON_OFF": "unlocked",
                             "ON_ON": "unlocked",
                             "OFF": "error"
                             }
                }

    run_tests("door_open", ["unlocked", "unlocked"], test_set, state_machine)


def test_error_state():
    """Test if error handling is OK"""
    function_name = inspect.currentframe().f_code.co_name
    print("\n########## %s #########", function_name)

    state_machine = door_lock_statemachine(
        name=function_name, logger=log)

    # check error map
    assert state_machine.cond_error() is False
    state_machine.set_lock_error(state_machine.JAMMED, True)
    assert state_machine.cond_error() is True
    state_machine.set_lock_error(state_machine.CONFIG_PENDING, True)
    assert state_machine.cond_error() is True
    state_machine.set_lock_error(state_machine.JAMMED, False)
    assert state_machine.cond_error() is True
    state_machine.set_lock_error(state_machine.UNREACHABLE, True)
    assert state_machine.cond_error() is True
    state_machine.set_lock_error(state_machine.UNREACHABLE, False)
    assert state_machine.cond_error() is True
    state_machine.set_lock_error(state_machine.CONFIG_PENDING, False)
    assert state_machine.cond_error() is False

    # check illegal error state
    state_machine.set_lock_error("UNKNOWN", True)
    assert state_machine.cond_error() is False

    state_machine.set_lock_error(state_machine.JAMMED, True)
    state_machine.send("tr_error_change")
    test_state(state_machine, "error")

    state_machine.set_lock_error(state_machine.JAMMED, False)
    state_machine.send("tr_error_change")
    test_state(state_machine, "unlocked")

    state_machine.set_lock_error(state_machine.JAMMED, True)
    state_machine.send("tr_error_change")
    test_state(state_machine, "error")

    # check dark
    state_machine.set_dark_outside(True)
    state_machine.send("tr_dark_outside_change")
    test_state(state_machine, "error")

    state_machine.set_dark_outside(False)
    state_machine.send("tr_dark_outside_change")
    test_state(state_machine, "error")

    # check door open
    state_machine.set_door_open(True)
    state_machine.send("tr_door_open_change")
    test_state(state_machine, "error")

    state_machine.set_door_open(False)
    state_machine.send("tr_door_open_change")
    test_state(state_machine, "error")

    # check light
    state_machine.set_light(True)
    state_machine.send("tr_light_change")
    test_state(state_machine, "error")

    state_machine.set_light(False)
    state_machine.send("tr_light_change")
    test_state(state_machine, "error")

    # reported reported lock state
    state_machine.set_reported_lock(state_machine.LOCKED)
    state_machine.send("tr_reported_lock_change")
    test_state(state_machine, "error")

    state_machine.set_reported_lock(state_machine.UNLOCKED)
    state_machine.send("tr_reported_lock_change")
    test_state(state_machine, "error")

    # check presence
    state_machine.set_presence(True)
    state_machine.send("tr_presence_change")
    test_state(state_machine, "error")

    state_machine.set_presence(False)
    state_machine.send("tr_presence_change")
    test_state(state_machine, "error")


def test_light_state():
    """Test if light state is OK"""
    function_name = inspect.currentframe().f_code.co_name
    print("\n########## %s #########", function_name)

    state_machine = door_lock_statemachine(
        name=function_name, logger=log)

    test_set = {"dark_outside": {"ON": "unlocked",
                                 "ON_OFF": "locked",
                                 "ON_ON": "unlocked",
                                 "OFF": "unlocked"
                                 },
                "door_open": {"ON": "unlocked",
                              "ON_OFF": "unlocked",
                              "ON_ON": "unlocked",
                              "OFF": "unlocked"
                              },
                "presence": {"ON": "unlocked",
                             "ON_OFF": "unlocked",
                             "ON_ON": "unlocked",
                             "OFF": "locked"
                             }
                }

    run_tests("light", ["unlocked", "unlocked"], test_set, state_machine)


def test_presence_state():
    """Test if presence state is OK"""
    function_name = inspect.currentframe().f_code.co_name
    print("\n########## %s #########", function_name)

    state_machine = door_lock_statemachine(
        name=function_name, logger=log)

    test_set = {"dark_outside": {"ON": "locked",
                                 "ON_OFF": "locked",
                                 "ON_ON": "locked",
                                 "OFF": "locked"
                                 },
                "door_open": {"ON": "error",
                              "ON_OFF": "error",
                              "ON_ON": "unlocked",
                              "OFF": "unlocked"
                              },
                "light": {"ON": "unlocked",
                          "ON_OFF": "locked",
                          "ON_ON": "unlocked",
                          "OFF": "unlocked"
                          },
                }

    run_tests("presence", ["unlocked", "locked"], test_set, state_machine)

    test_set = {  # use this twice to start checking door_open in unlocked state
        "door_open": {"ON": "unlocked",
                      "ON_OFF": "error",
                      "ON_ON": "unlocked",
                      "OFF": "unlocked"
                      },
    }

    run_tests("presence", ["unlocked", "locked"], test_set, state_machine)


def test_reported_lock_state():
    """Test if reported lock state handling is OK"""
    function_name = inspect.currentframe().f_code.co_name
    print("\n########## %s #########", function_name)

    state_machine = door_lock_statemachine(
        name=function_name, logger=log)

    # check error map
    assert state_machine.get_reported_lock() is False
    state_machine.set_reported_lock(state_machine.LOCKED)
    assert state_machine.get_reported_lock() is True
    state_machine.set_reported_lock(state_machine.UNLOCKED)
    assert state_machine.get_reported_lock() is False

    # check illegal error state
    state_machine.set_reported_lock("UNKNOWN")
    assert state_machine.get_reported_lock() is False

    state_machine.set_reported_lock(state_machine.LOCKED)
    state_machine.send("tr_reported_lock_change")
    test_state(state_machine, "locked")

    state_machine.set_reported_lock(state_machine.UNLOCKED)
    state_machine.send("tr_reported_lock_change")
    test_state(state_machine, "unlocked")


test_default_state()
test_dark_outside_state()
test_door_open_state()
test_error_state()
test_reported_lock_state()
test_light_state()
test_presence_state()
