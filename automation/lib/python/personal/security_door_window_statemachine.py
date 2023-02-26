"""StateMachine for Homematic-IP MP3-Player colors """
import sys
import os
import platform

# log:set INFO jsr223.jython.Thermostat_statemachines_create

OH_CONF = os.getenv('OPENHAB_CONF')
LIGHT_LEVEL = 60

sys.path.append(os.path.join(OH_CONF, "automation/lib/python/personal"))
from statemachine import State, StateMachine


scriptpath = os.path.join(OH_CONF, "automation/jsr223/python/personal")

sys.path.append("/home/openhabian/git/python-statemachine")
from statemachine.contrib.diagram import DotGraphMachine


def get_state_machine_graph(sm):
    """create the PNG of the statemachine
    Args:
        sm_name (string): instance of the statemachine
    Returns:
        None
    """
    if (platform.system() == "Windows"):
        return

    # also accepts instances
    graph = DotGraphMachine(sm)
    graph().write_png(os.path.join(scriptpath, "images",
                                   sm.get_name() + "_door_window_color_sm.png"))


def get_internal_state_machine_state(sm):
    """log internal states
    Args:
        sm (string): statemachine where info is wanted
    Returns:
        string: internal info for all states
    """
    info = "Internal machine states (" + str(sm.get_name()) + "):"
    info += "\n   state            = " + str(sm.get_state_name())
    info += "\n   _bell_rang       = " + str(sm.get_bell_rang())
    info += "\n   _lock_error      = " + str(sm.get_lock_error())
    info += "\n   _outer_door_open = " + str(sm.get_outer_door_open())
    info += "\n   _timeout         = " + str(sm.get_timeout())
    info += "\n   _window_open     = " + str(sm.get_window_open())
    return info


class security_door_window_statemachine(StateMachine):
    "handle state of DoorLock"

    # States
    st_black = State("black", initial=True)
    st_blue = State("blue")
    st_green = State("green")
    st_purple = State("purple")
    st_red = State("red")
    st_yellow = State("yellow")

    # Transitions
    tr_bell_rang = (st_black.to(st_yellow, cond="cond_bell_rang") |
                    st_blue.to(st_yellow, cond="cond_bell_rang") |
                    st_green.to(st_yellow, cond="cond_bell_rang") |
                    st_green.to.itself() |
                    st_purple.to(st_yellow, cond="cond_bell_rang") |
                    st_red.to.itself() |
                    st_yellow.to.itself(cond="cond_bell_rang") |
                    st_yellow.to(st_purple, cond="cond_outer_door_open") |
                    st_yellow.to(st_blue, cond="cond_window_open") |
                    st_yellow.to(st_green) |
                    st_black.to.itself()
                   )

    tr_lock_error = (st_black.to(st_red, cond="cond_lock_error") |
                     st_blue.to(st_red, cond="cond_lock_error") |
                     st_green.to(st_red, cond="cond_lock_error") |
                     st_purple.to(st_red, cond="cond_lock_error") |
                     st_red.to(st_red, cond="cond_lock_error") |
                     st_yellow.to(st_red, cond="cond_lock_error") |
                     st_red.to(st_yellow, cond="cond_bell_rang") |
                     st_red.to(st_purple, cond="cond_outer_door_open") |
                     st_red.to(st_blue, cond="cond_window_open") |
                     st_red.to(st_green) |
                     st_black.to.itself()
                    )

    tr_outer_door_open = (st_black.to(st_purple, cond="cond_outer_door_open") |
                          st_blue.to(st_purple, cond="cond_outer_door_open") |
                          st_green.to(st_purple, cond="cond_outer_door_open") |
                          st_purple.to.itself(cond="cond_outer_door_open") |
                          st_red.to.itself() |
                          st_yellow.to.itself() |
                          st_purple.to(st_blue, cond="cond_window_open") |
                          st_purple.to(st_green) |
                          st_black.to.itself()
                         )

    tr_window_open = (st_black.to(st_blue, cond="cond_window_open") |
                      st_blue.to(st_blue, cond="cond_window_open") |
                      st_green.to(st_blue, cond="cond_window_open") |
                      st_purple.to.itself() |
                      st_red.to.itself() |
                      st_yellow.to.itself() |
                      st_blue.to(st_green) |
                      st_black.to.itself()
                     )

    tr_timeout = (st_black.to.itself() |
                  st_blue.to.itself(cond="cond_window_open") |
                  st_blue.to(st_black) |
                  st_green.to(st_black) |
                  st_purple.to.itself() |
                  st_red.to.itself() |
                  st_yellow.to(st_purple, cond="cond_outer_door_open") |
                  st_yellow.to(st_blue, cond="cond_window_open") |
                  st_yellow.to(st_green)
                 )

    def __init__(self, name="unnamed", logger=None):
        # variables
        self._mp3_player_name = name
        self._logger = logger

        self._bell_rang = False
        self._lock_error = False
        self._outer_door_open = False
        self._timeout = False
        self._window_open = False

        self._light_level = 0

#        for name, value in os.environ.items():
#            self._logger.debug("{0}: {1}".format(name, value))

        super(security_door_window_statemachine, self).__init__()

        get_state_machine_graph(self)

    def get_bell_rang(self):
        """return the state of the bell_rang
        Returns:
            bool: bell_rang state
        """
        return self._bell_rang

    def get_lock_error(self):
        """return the state of the lock_error
        Returns:
            bool: lock_error state
        """

        return self._lock_error

    def get_outer_door_open(self):
        """return the state of the outer_door_open
        Returns:
            bool: outer_door_open state
        """
        return self._outer_door_open

    def get_timeout(self):
        """return the state of the timeout
        Returns:
            bool: timeout state
        """
        return self._timeout

    def get_window_open(self):
        """return the state of the light
        Returns:
            bool: light state
        """
        return self._window_open

    def get_name(self):
        """return the name of the statemachine
        Returns:
            string: name
        """
        return self._mp3_player_name

    def get_state_name(self):
        """return the current state of the statemachine
        Returns:
            string: state name
        """
        return self.current_state.name.upper()

    def get_light_level(self):
        """return the level (0..100) of the light
        Returns:
            bool: light level
        """
        return self._light_level

    # set internal states BEFORE the event is send
    def set_bell_rang(self, state):
        """set internal state of bell_rang
        Args:
            state (bool): state of bell_rang
        """
        self._bell_rang = state
        self._logger.info(
            self.get_name() + ": - bell rang is: " + str(self._bell_rang))

    def set_lock_error(self, state):
        """set internal state of lock_error
        Args:
            state (bool): state of presence
        """
        self._lock_error = state
        self._logger.info(
            self.get_name() + ": - lock error is: " + str(self._lock_error))

    def set_outer_door_open(self, state):
        """set internal state of outer_door_open
        Args:
            state (bool): state of outer_door_open
        """
        self._outer_door_open = state
        self._logger.info(self.get_name() +
                          ": - outer door open is: " + str(self._outer_door_open))

    def set_timeout(self, state):
        """set internal state of timeout
        Args:
            state (bool): state of timeout
        """
        self._timeout = state
        self._logger.info(self.get_name() +
                          ": - outer door open is: " + str(self._timeout))

    def set_window_open(self, state):
        """set internal state of light
        Args:
            state (bool): state of light
        """
        self._window_open = state
        self._logger.info(self.get_name() + ": - window open is: " + str(self._window_open))

    # Conditions
    def cond_bell_rang(self):
        """check if it is dark outside
        Returns:
            boolean: True/False
        """
        self._logger.debug(self.get_name() + ": bell_rang = '{}'.".format(str(self._bell_rang)))
        return self._bell_rang

    def cond_outer_door_open(self):
        """check if door is open
        Returns:
            boolean: True/False
        """
        self._logger.debug(self.get_name() + ": outer_door_open = '{}'.".format(str(self._outer_door_open)))
        return self._outer_door_open

    def cond_lock_error (self):
        """rule to decide if the lock is in an "error" state
        Returns:
            boolean: True/False
        """

        self._logger.debug(self.get_name() + ": lock_error = '{}'.".format(str(self._lock_error)))

        return self._lock_error

    def cond_window_open(self):
        """check if window is open
        Returns:
            boolean: True/False
        """
        self._logger.debug(self.get_name() + ": light = '" + str(self._window_open) + "'.")
        return self._window_open


    # see https://python-statemachine.readthedocs.io/en/latest/actions.html#ordering
    def before_transition(self, event, state):
        """events received for any state """
        self._logger.debug(self.get_name() + "(" + str(id(self)) +
                           "): Before   '{}' in '{}' state.".format(event, state.id))

    def on_enter_state(self, event, state):
        """entry function for any state """
        self._logger.debug(self.get_name() + "(" + str(id(self)) +
                           "): Entering '{}' state triggered by '{}' event.".format(state.id, event))

    def after_transition(self, event, state):
        """last function in state change queue """
        self._logger.debug(
            self.get_name() + ": is in state {}.".format(state.id))

    def on_enter_st_black(self, source, target):
        """entry action for state st_black"""
        if source != target:
            self._light_level = 0
            self._logger.debug(
                self.get_name() + ": set light level to %d", self._light_level)
        else:
            self._logger.debug(
                self.get_name() + ": internal transition")

    def on_exit_st_black(self, source, target):
        """entry action for state st_black"""
        if source != target:
            self._light_level = LIGHT_LEVEL
            self._logger.debug(
                self.get_name() + ": set light level to %d", self._light_level)
        else:
            self._logger.debug(
                self.get_name() + ": internal transition")
