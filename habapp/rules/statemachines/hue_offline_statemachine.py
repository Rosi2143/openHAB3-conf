"""StateMachine for handling hue offline problem """

import sys
import os
import platform

# log:set INFO jsr223.jython.hue_offline

OH_CONF = "/etc/openhab/"  # os.getenv('OPENHAB_CONF')
scriptpath = os.path.join(OH_CONF, "habapp")

from statemachine import State, StateMachine
from statemachine.contrib.diagram import DotGraphMachine


hue_offline_list = {}


def get_state_machine_list():
    """get the list with all statemachines"""
    return hue_offline_list


def get_state_machine(item_name, logger):
    """make sure a statemachine exists for the item
    Args:
        item_name (string): name of the item <thing_name>_<itempart>
        logger (object): pass the logger for tracing
    Returns:
        new or existing statemachine
    """
    thing_name = item_name.split("_")[0]
    if thing_name not in hue_offline_list:
        hue_offline_list[thing_name] = HueOfflineStatemachine(thing_name, logger)
        logger.info(
            "Created HueOfflineSm: ("
            + str(id(hue_offline_list[thing_name]))
            + "):"
            + hue_offline_list[thing_name].get_name()
        )

        if platform.system() != "Windows":
            # also accepts instances
            graph = DotGraphMachine(hue_offline_list[thing_name])
            imagepath = os.path.join(scriptpath, "images")
            if not os.path.exists(imagepath):
                os.makedirs(imagepath)
            graph().write_png(
                os.path.join(
                    imagepath,
                    hue_offline_list[thing_name].get_name() + "_hue_offline_sm.png",
                )
            )
    else:
        logger.info(
            "Use existing HueOfflineSm ("
            + str(id(hue_offline_list[thing_name]))
            + "): "
            + hue_offline_list[thing_name].get_name()
        )

    return hue_offline_list[thing_name]


def get_internal_state_machine_state(sm):
    """_summary_
    Args:
        sm (string): statemachine where info is wanted
    Returns:
        string: internal info for all states
    """
    info = "Internal machine states (" + str(sm.get_name()) + "):"
    info += "\n   state        = " + str(sm.get_state_name())
    info += "\n   _state       = " + str(sm.cond_state_is_active())
    info += "\n   _offline     = " + str(sm.cond_offline_is_active())
    return info


class HueOfflineStatemachine(StateMachine):
    "handle state of Hue Things"

    # States
    st_online_off = State("online_off", initial=True)
    st_online_on = State("online_on")
    st_offline = State("offline")

    # Transitions
    tr_online_change = (
        st_online_on.to(st_offline, cond="cond_offline_is_active")
        | st_online_on.to(
            st_online_off, unless=["cond_offline_is_active", "cond_state_is_active"]
        )
        | st_online_on.to.itself()
        | st_online_off.to(st_offline, cond="cond_offline_is_active")
        | st_online_off.to(
            st_online_on, unless="cond_offline_is_active", cond="cond_state_is_active"
        )
        | st_online_off.to.itself()
        | st_offline.to(
            st_online_off, unless=["cond_offline_is_active", "cond_state_is_active"]
        )
        | st_offline.to(
            st_online_on, unless="cond_offline_is_active", cond="cond_state_is_active"
        )
        | st_offline.to.itself()
    )

    tr_state_change = (
        st_online_on.to(st_online_off, unless="cond_state_is_active")
        | st_online_on.to.itself()
        | st_online_off.to(st_online_on, cond="cond_state_is_active")
        | st_online_off.to.itself()
        | st_offline.to.itself()
    )

    def __init__(self, name="unnamed", logger=None):
        # variables
        self._hue_thing_name = name
        self._logger = logger

        self._offline = False
        self._state = False

        #        for name, value in os.environ.items():
        #            self._logger.debug("{0}: {1}".format(name, value))

        super(HueOfflineStatemachine, self).__init__()

    def get_name(self):
        """return the name of the statemachine
        Returns:
            string: name
        """
        return self._hue_thing_name

    def get_state_name(self):
        """return the current state of the statemachine
        Returns:
            string: state name
        """
        return self.current_state.name

    # set internal states BEFORE the event is send
    def set_offline(self, state):
        """set internal state of offline
        Args:
            state (bool): state of offline
        """
        self._offline = state
        self._logger.info(
            self.get_name()
            + "("
            + str(id(self))
            + "): - offline is: "
            + str(self._offline)
        )

    def set_state(self, state):
        """set internal state of offline
        Args:
            state (bool): state of offline
        """
        self._state = state
        self._logger.info(
            self.get_name() + "(" + str(id(self)) + "): - state is: " + str(self._state)
        )

    # Conditions
    def cond_offline_is_active(self):
        """check if offline mode is active
        Returns:
            boolean: True/False
        """
        self._logger.debug(
            self.get_name()
            + "("
            + str(id(self))
            + "): offline = '"
            + str(self._offline)
            + "'."
        )
        return self._offline

    def cond_state_is_active(self):
        """check if state mode is active
        Returns:
            boolean: True/False
        """
        self._logger.debug(
            self.get_name()
            + "("
            + str(id(self))
            + "): state = '"
            + str(self._state)
            + "'."
        )
        return self._state

    # see https://python-statemachine.readthedocs.io/en/latest/actions.html#ordering
    def before_transition(self, event, state):
        """events received for any state"""
        self._logger.debug(
            self.get_name()
            + "("
            + str(id(self))
            + "): Before   '{}' in '{}' state.".format(event, state.id)
        )

    def on_enter_state(self, event, state):
        """entry function for any state"""
        self._logger.debug(
            self.get_name()
            + "("
            + str(id(self))
            + "): Entering '{}' state triggered by '{}' event.".format(state.id, event)
        )

    def after_transition(self, event, state):
        """last function in state change queue"""
        self._logger.info(
            self.get_name()
            + "("
            + str(id(self))
            + "): is in state {}.".format(state.id)
        )
