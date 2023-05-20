"""Example of python module statemachine: https://pypi.org/project/python-statemachine/"""

import sys
import os
import logging
import inspect

from statemachine import State
from statemachine import StateMachine


class TestStateMachine(StateMachine):
    """simple statemachine to test features

    Args:
        StateMachine (BaseClass):

    Returns:
        none
    """
    green = State("Green", initial=True)
    yellow = State("Yellow")
    red = State("Red")
    blue = State("Blue")
    purple = State("Purple")

    cycle = (green.to(yellow) |
             yellow.to(red) |
             red.to(green) |
             blue.to.itself() |
             purple.to.itself())

    check = (green.to(blue, cond="is_true") |
             green.to(purple, cond="is_false") |
             yellow.to.itself() |
             red.to.itself() |
             blue.to.itself() |
             purple.to.itself())

    def __init__(self, logger=None):
        # variables
        self._logger = logger
        self._state = False
        super(TestStateMachine, self).__init__()

    def set_state(self, state):
        """used to test condition functions
        """
        self._state = state

    def is_true(self):
        """used to test condition functions
        """
        return self._state

    def is_false(self):
        """used to test condition functions
        """
        return not self._state

    def on_transition(self, event_data=None):
        """print debug info for event cycle
        """
        self._logger.info("Running {} from {} to {}".format(
            event_data.event,
            event_data.source.id,
            event_data.target.id,
        ))


OH_CONF = os.getenv('OPENHAB_CONF')

sys.path.append(os.path.join(OH_CONF, "automation/lib/python/personal"))
sys.path.append(os.path.join(OH_CONF, "automation/lib/python"))

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


def test_default_state():
    """Test if default (initial) state is OK
    """
    function_name = inspect.currentframe().f_code.co_name
    print("\n########## %s #########", function_name)

    state_machine = TestStateMachine(log)
    log.debug(state_machine.current_state.id)
    assert state_machine.current_state.id == "green"

    state_machine.send("cycle")


def test_conditions_state_true():
    """Test if default (initial) state is OK
    """
    function_name = inspect.currentframe().f_code.co_name
    print("\n########## %s #########", function_name)

    state_machine = TestStateMachine(log)
    log.debug(state_machine.current_state.id)

    state_machine.set_state(True)
    state_machine.send("check")
    print(f"state: {state_machine.current_state.id}")
    assert state_machine.current_state.id == "blue"


def test_conditions_state_false():
    """Test if default (initial) state is OK
    """
    function_name = inspect.currentframe().f_code.co_name
    print("\n########## %s #########", function_name)

    state_machine = TestStateMachine(log)
    log.debug(state_machine.current_state.id)

    state_machine.set_state(False)
    state_machine.send("check")
    print(f"state: {state_machine.current_state.id}")
    assert state_machine.current_state.id == "purple"


def test_missing_transition():
    """Test if default (initial) state is OK
    """
    function_name = inspect.currentframe().f_code.co_name
    print("\n########## %s #########", function_name)

    state_machine = TestStateMachine(log)
    log.debug(state_machine.current_state.id)

    state_machine.set_state(True)
    state_machine.send("check")
    print(f"state: {state_machine.current_state.id}")

    state_machine.send("cycle")
    state_machine.send("check")


test_default_state()
test_conditions_state_true()
test_conditions_state_false()
test_missing_transition()
