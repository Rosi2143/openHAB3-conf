"""Example of python module statemachine: https://pypi.org/project/python-statemachine/
Tests only pass with version 1.0.3 and later (6dbc55c1595301f5a80557c70a7b3a57f459ad80)
"""

import logging


from statemachine import State, StateMachine

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


class TestStateMachine(StateMachine):

    # States
    st_1 = State("One", initial=True)
    st_2 = State("Two")
    st_3 = State("Three")

    def __init__(self, name="unnamed"):
        # variables
        self.sm_name = name

        self.one = False
        self.two = True
        self.three = True

        super(TestStateMachine, self).__init__()

    # Transitions
    tr_change = (st_1.to(st_1, cond="cond_one_is_active") |
                 st_1.to(st_2, cond="cond_two_is_active") |
                 st_1.to(st_3, cond="cond_three_is_active") |
                 st_2.to(st_1, cond="cond_one_is_active") |
                 st_2.to(st_2, cond="cond_two_is_active") |
                 st_2.to(st_3, cond="cond_three_is_active"))
    # Conditions

    def cond_one_is_active(self):
        return self.one

    def cond_two_is_active(self):
        return self.two

    def cond_three_is_active(self):
        return self.three


def test_state(state_machine, state):
    print(state_machine.current_state.name)
    assert state_machine.current_state.name == state


def test_single_sm():

    sm = TestStateMachine()
    test_state(sm, "One")
    sm.send("tr_change")
    test_state(sm, "Two")


def test_multiple_sm():

    sm_list = {}
    for index in [0, 1, 2]:
        sm_list[index] = TestStateMachine(str(index))
        print(sm_list[index].sm_name)
        test_state(sm_list[index], "One")

        sm_list[index].send("tr_change")
        test_state(sm_list[index], "Two")

    test_index = 0
    sm_list[test_index].two = False
    sm_list[test_index].send("tr_change")
    test_state(sm_list[test_index], "Three")


test_single_sm()
test_multiple_sm()
