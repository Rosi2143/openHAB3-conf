"""Example of python module statemachine: https://pypi.org/project/python-statemachine/"""

import sys
import os
import logging
import inspect
import time
from datetime import datetime, timedelta


OH_CONF = os.getenv("OPENHAB_CONF")

print("OH_CONF = " + OH_CONF)

sys.path.append(OH_CONF + "/habapp/rules/")
from statemachines.IndegoStatemachine import IndegoStatemachine

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
    log.debug(
        "assert: %s [current]%s == [expect]%s",
        state_machine.get_name(),
        state_machine.current_state.name,
        state,
    )
    assert state_machine.current_state.name == state


def test_time(
    time_test, state_machine, expected_time, calculated_time, allowed_delta_sec=1
):
    """make testing of times easier"""
    expected_time_str = state_machine.format_time(expected_time)
    calculated_time_str = state_machine.format_time(calculated_time)
    time_delta = abs(expected_time - calculated_time)
    log.info(
        "assert: %s - [calculated time]%s == [expect time]%s -- delta = %s",
        time_test,
        calculated_time_str,
        expected_time_str,
        state_machine.format_time(time_delta),
    )
    assert time_delta < timedelta(seconds=(allowed_delta_sec + 1))


def check_times(
    state_machine, mow_start_time, mow_duration, pause_start_time, pause_duration
):
    test_time(
        "mow_start_time  ",
        state_machine,
        mow_start_time,
        state_machine.get_mow_start_time(),
    )
    test_time(
        "mow_duration    ",
        state_machine,
        mow_duration,
        state_machine.get_mow_duration(),
    )
    test_time(
        "pause_start_time",
        state_machine,
        pause_start_time,
        state_machine.get_pause_start_time(),
    )
    test_time(
        "pause_duration  ",
        state_machine,
        pause_duration,
        state_machine.get_pause_duration(),
    )


def run_tests(test_set, transition):
    """Run all tests of the test_set"""

    for new_state, target_state in test_set.items():
        # initialize test statemachine
        print(f"\nhandling new state -- {new_state}")
        state_machine = IndegoStatemachine(name=transition, logger=log)
        state_machine.set_reported_state(transition)

        state_machine.set_reported_state(new_state)
        test_state(state_machine, target_state)


def test_default_state():
    """Test if default (initial) state is OK"""
    function_name = inspect.currentframe().f_code.co_name
    print(f"\n########## {function_name} #########")

    state_machine = IndegoStatemachine(name="TestMachine", logger=log)

    test_state(state_machine, state_machine.STATUS_UNKNOWN)


def test_init_state():
    """Test unknwon state is OK"""
    function_name = inspect.currentframe().f_code.co_name
    print(f"\n########## {function_name} #########")

    state_machine = IndegoStatemachine(name="TestMachine", logger=log)
    test_set = {
        "Border cut": state_machine.STATUS_MOW,
        "Charging": state_machine.STATUS_DOCK,
        "Docked": state_machine.STATUS_DOCK,
        "Docked - Saving map": state_machine.STATUS_DOCK,
        "Idle in lawn": state_machine.STATUS_PAUSE,
        "Mowing": state_machine.STATUS_MOW,
        "Paused": state_machine.STATUS_PAUSE,
        "Relocalising": state_machine.STATUS_PAUSE,
        "Returning to Dock": state_machine.STATUS_MOWING_COMPLETE,
        "Returning to Dock - Battery low": state_machine.STATUS_PAUSE,
        "Returning to Dock - Lawn complete": state_machine.STATUS_MOWING_COMPLETE,
        "SpotMow": state_machine.STATUS_MOW,
    }

    run_tests(test_set, "Init")


def test_mow_state():
    """Test mow state is OK"""
    function_name = inspect.currentframe().f_code.co_name
    print(f"\n########## {function_name} #########")

    state_machine = IndegoStatemachine(name="TestMachine", logger=log)
    test_set = {
        "Border cut": state_machine.STATUS_MOW,
        "Charging": state_machine.STATUS_DOCK,
        "Docked": state_machine.STATUS_DOCK,
        "Docked - Saving map": state_machine.STATUS_DOCK,
        "Idle in lawn": state_machine.STATUS_PAUSE,
        "Mowing": state_machine.STATUS_MOW,
        "Paused": state_machine.STATUS_PAUSE,
        "Relocalising": state_machine.STATUS_PAUSE,
        "Returning to Dock": state_machine.STATUS_MOWING_COMPLETE,
        "Returning to Dock - Battery low": state_machine.STATUS_PAUSE,
        "Returning to Dock - Lawn complete": state_machine.STATUS_MOWING_COMPLETE,
        "SpotMow": state_machine.STATUS_MOW,
    }

    run_tests(test_set, "Mowing")


def test_mowing_complete_state():
    """Test mow state is OK"""
    function_name = inspect.currentframe().f_code.co_name
    print(f"\n########## {function_name} #########")

    state_machine = IndegoStatemachine(name="TestMachine", logger=log)
    test_set = {
        "Border cut": state_machine.STATUS_MOW,
        "Charging": state_machine.STATUS_DOCK,
        "Docked": state_machine.STATUS_DOCK,
        "Docked - Saving map": state_machine.STATUS_DOCK,
        "Idle in lawn": state_machine.STATUS_PAUSE,
        "Mowing": state_machine.STATUS_MOW,
        "Paused": state_machine.STATUS_PAUSE,
        "Relocalising": state_machine.STATUS_PAUSE,
        "Returning to Dock": state_machine.STATUS_MOWING_COMPLETE,
        "Returning to Dock - Battery low": state_machine.STATUS_PAUSE,
        "Returning to Dock - Lawn complete": state_machine.STATUS_MOWING_COMPLETE,
        "SpotMow": state_machine.STATUS_MOW,
    }

    run_tests(test_set, "Mowing")


def test_pause_state():
    """Test pause state is OK"""
    function_name = inspect.currentframe().f_code.co_name
    print(f"\n########## {function_name} #########")

    state_machine = IndegoStatemachine(name="TestMachine", logger=log)
    test_set = {
        "Border cut": state_machine.STATUS_MOW,
        "Charging": state_machine.STATUS_DOCK,
        "Docked": state_machine.STATUS_PAUSE,
        "Docked - Saving map": state_machine.STATUS_PAUSE,
        "Idle in lawn": state_machine.STATUS_PAUSE,
        "Mowing": state_machine.STATUS_MOW,
        "Paused": state_machine.STATUS_PAUSE,
        "Relocalising": state_machine.STATUS_PAUSE,
        "Returning to Dock": state_machine.STATUS_MOWING_COMPLETE,
        "Returning to Dock - Battery low": state_machine.STATUS_PAUSE,
        "Returning to Dock - Lawn complete": state_machine.STATUS_MOWING_COMPLETE,
        "SpotMow": state_machine.STATUS_MOW,
    }

    run_tests(test_set, "Paused")


def test_dock_state():
    """Test dock state is OK"""
    function_name = inspect.currentframe().f_code.co_name
    print(f"\n########## {function_name} #########")

    state_machine = IndegoStatemachine(name="TestMachine", logger=log)
    test_set = {
        "Border cut": state_machine.STATUS_MOW,
        "Charging": state_machine.STATUS_DOCK,
        "Docked": state_machine.STATUS_DOCK,
        "Docked - Saving map": state_machine.STATUS_DOCK,
        "Idle in lawn": state_machine.STATUS_PAUSE,
        "Mowing": state_machine.STATUS_MOW,
        "Paused": state_machine.STATUS_PAUSE,
        "Relocalising": state_machine.STATUS_PAUSE,
        "Returning to Dock": state_machine.STATUS_MOWING_COMPLETE,
        "Returning to Dock - Battery low": state_machine.STATUS_PAUSE,
        "Returning to Dock - Lawn complete": state_machine.STATUS_MOWING_COMPLETE,
        "SpotMow": state_machine.STATUS_MOW,
    }

    run_tests(test_set, "Docked")


def test_time_calculation():
    """Test if times are calculated correctly"""
    function_name = inspect.currentframe().f_code.co_name
    print(f"\n########## {function_name} #########")

    SLEEP_TIME_SEC = 5
    test_start = datetime.now()
    mowing_time = timedelta(0)
    pause_time = timedelta(0)
    state_machine = IndegoStatemachine(name="TestMachine", logger=log)
    check_times(state_machine, datetime.min, timedelta(0), datetime.min, timedelta(0))

    # get out of Init state
    state_machine.set_reported_state("Mowing")
    state_machine.set_reported_state("Docked")

    # start moving cycle
    state_machine.set_reported_state("Border cut")
    check_times(state_machine, test_start, timedelta(0), datetime.min, timedelta(0))
    time.sleep(SLEEP_TIME_SEC)
    mowing_time = mowing_time + timedelta(seconds=SLEEP_TIME_SEC)

    state_machine.set_reported_state("Relocalising")
    check_times(state_machine, test_start, timedelta(0), datetime.now(), timedelta(0))
    time.sleep(SLEEP_TIME_SEC)
    pause_time = pause_time + timedelta(seconds=SLEEP_TIME_SEC)

    state_machine.set_reported_state("Mowing")
    check_times(
        state_machine=state_machine,
        mow_start_time=test_start,
        mow_duration=timedelta(0),
        pause_start_time=datetime.min,
        pause_duration=pause_time,
    )
    time.sleep(SLEEP_TIME_SEC)
    mowing_time = mowing_time + timedelta(seconds=SLEEP_TIME_SEC)

    state_machine.set_reported_state("Returning to Dock - Battery low")
    check_times(
        state_machine=state_machine,
        mow_start_time=test_start,
        mow_duration=timedelta(0),
        pause_start_time=datetime.now(),
        pause_duration=pause_time,
    )
    time.sleep(SLEEP_TIME_SEC)
    pause_time = pause_time + timedelta(seconds=SLEEP_TIME_SEC)

    state_machine.set_reported_state("Docked")
    check_times(
        state_machine=state_machine,
        mow_start_time=test_start,
        mow_duration=timedelta(0),
        pause_start_time=datetime.now() - timedelta(seconds=SLEEP_TIME_SEC),
        pause_duration=pause_time,
    )
    time.sleep(SLEEP_TIME_SEC)
    pause_time = pause_time + timedelta(seconds=SLEEP_TIME_SEC)

    state_machine.set_reported_state("Mowing")
    check_times(
        state_machine=state_machine,
        mow_start_time=test_start,
        mow_duration=timedelta(0),
        pause_start_time=datetime.min,
        pause_duration=pause_time,
    )
    time.sleep(SLEEP_TIME_SEC)
    mowing_time = mowing_time + timedelta(seconds=SLEEP_TIME_SEC)

    state_machine.set_reported_state("Idle in lawn")
    check_times(
        state_machine=state_machine,
        mow_start_time=test_start,
        mow_duration=timedelta(0),
        pause_start_time=datetime.now(),
        pause_duration=pause_time,
    )
    time.sleep(SLEEP_TIME_SEC)
    pause_time = pause_time + timedelta(seconds=SLEEP_TIME_SEC)

    state_machine.set_reported_state("Relocalising")
    check_times(
        state_machine=state_machine,
        mow_start_time=test_start,
        mow_duration=timedelta(0),
        pause_start_time=datetime.now() - timedelta(seconds=SLEEP_TIME_SEC),
        pause_duration=pause_time,
    )
    time.sleep(SLEEP_TIME_SEC)
    pause_time = pause_time + timedelta(seconds=SLEEP_TIME_SEC)

    state_machine.set_reported_state("Mowing")
    check_times(
        state_machine=state_machine,
        mow_start_time=test_start,
        mow_duration=timedelta(0),
        pause_start_time=datetime.min,
        pause_duration=pause_time,
    )
    time.sleep(SLEEP_TIME_SEC)
    mowing_time = mowing_time + timedelta(seconds=SLEEP_TIME_SEC)

    state_machine.set_reported_state("Returning to Dock - Lawn complete")
    check_times(
        state_machine=state_machine,
        mow_start_time=test_start,
        mow_duration=timedelta(0),
        pause_start_time=datetime.now(),
        pause_duration=pause_time,
    )
    time.sleep(SLEEP_TIME_SEC)
    pause_time = pause_time + timedelta(seconds=SLEEP_TIME_SEC)

    state_machine.set_reported_state("Docked")
    check_times(
        state_machine=state_machine,
        mow_start_time=datetime.min,
        mow_duration=mowing_time,
        pause_start_time=datetime.min,
        pause_duration=timedelta(0),
    )
    time.sleep(SLEEP_TIME_SEC)

    state_machine.set_reported_state("Charging")
    check_times(
        state_machine=state_machine,
        mow_start_time=datetime.min,
        mow_duration=mowing_time,
        pause_start_time=datetime.min,
        pause_duration=timedelta(0),
    )
    time.sleep(SLEEP_TIME_SEC)

    state_machine.set_reported_state("Docked")
    check_times(
        state_machine=state_machine,
        mow_start_time=datetime.min,
        mow_duration=mowing_time,
        pause_start_time=datetime.min,
        pause_duration=timedelta(0),
    )


test_default_state()
test_init_state()
test_mow_state()
test_pause_state()
test_dock_state()
test_time_calculation()
