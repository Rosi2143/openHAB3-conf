"""StateMachine for Homematic-IP thermostats """
import sys
import os
import platform

# log:set INFO jsr223.jython.Thermostat_statemachines_create

OH_CONF = os.getenv('OPENHAB_CONF')

sys.path.append(os.path.join(OH_CONF, "automation/lib/python/personal"))
from statemachine import State, StateMachine


scriptpath = os.path.join(OH_CONF, "automation/jsr223/python/personal")

sys.path.append("/home/openhabian/git/python-statemachine")
from statemachine.contrib.diagram import DotGraphMachine

thermostate_list = {}


def get_state_machine_list():
    return thermostate_list


def get_state_machine(item_name, logger):
    """make sure a statemachine exists for the item
    Args:
        item_name (string): name of the item <thing_name>_<itempart>
        logger (object): pass the logger for tracing
    Returns:
        new or existing statemachine
    """
    thing_name = item_name.split("_")[0]
    if thing_name not in thermostate_list:
        thermostate_list[thing_name] = thermostat_statemachine(
            thing_name, logger)
        logger.info("Created ThermostatSm: (" + str(id(thermostate_list[thing_name])) + "):" +
                    thermostate_list[thing_name].get_name())

        if (platform.system() != "Windows"):
            # also accepts instances
            graph = DotGraphMachine(thermostate_list[thing_name])
            graph().write_png(os.path.join(scriptpath, "images",
                                           thermostate_list[thing_name].get_name() + "_thermostate_sm.png"))
    else:
        logger.info("Use existing ThermostatSm (" + str(id(thermostate_list[thing_name])) + "): " +
                    thermostate_list[thing_name].get_name())

    return thermostate_list[thing_name]


def get_internal_state_machine_state(sm):
    """_summary_
    Args:
        sm (string): statemachine where info is wanted
    Returns:
        string: internal info for all states
    """
    info = "Internal machine states (" + str(sm.get_name()) + "):"
    info += "\n   state        = " + str(sm.get_state_name())
    info += "\n   _boost       = " + str(sm.cond_boost_is_active())
    info += "\n   _config      = " + str(sm.cond_config_is_active())
    info += "\n   _mode        = " + str(sm.get_mode())
    info += "\n   _party       = " + str(sm.cond_party_is_active())
    info += "\n   _window_open = " + str(sm.cond_window_is_open())
    return info


class thermostat_statemachine(StateMachine):
    "handle state of thermostats"

    # constants
    AUTO = "auto"
    MANUAL = "manual"
    VACATION = "vacation"
    state_map = {"0": AUTO,
                 "1": MANUAL,
                 "2": VACATION}

    # States
    st_auto = State("auto", initial=True)
    st_boost = State("boost")
    st_config = State("config")
    st_manual = State("manual")
    st_off = State("off")
    st_party = State("party")
    st_vacation = State("vacation")

    # Transitions
    tr_boost_change = (st_auto.to(st_boost, cond="cond_boost_is_active") |
                       st_manual.to(st_boost, cond="cond_boost_is_active") |
                       st_party.to(st_boost, cond="cond_boost_is_active") |
                       st_vacation.to(st_boost, cond="cond_boost_is_active") |
                       st_boost.to(st_config, cond="cond_config_is_active") |
                       st_boost.to(st_off, cond="cond_window_is_open") |
                       st_boost.to.itself(cond="cond_boost_is_active") |
                       st_boost.to(st_vacation, cond="cond_mode_is_vacation") |
                       st_boost.to(st_party, cond="cond_party_is_active") |
                       st_boost.to(st_auto, cond="cond_mode_is_auto") |
                       st_boost.to.itself(cond="cond_mode_is_manual") |
                       st_auto.to.itself() |
                       st_boost.to.itself() |
                       st_config.to.itself() |
                       st_manual.to.itself() |
                       st_off.to.itself() |
                       st_party.to.itself() |
                       st_vacation.to.itself())

    tr_config_change = (st_auto.to(st_config, cond="cond_config_is_active") |
                        st_manual.to(st_config, cond="cond_config_is_active") |
                        st_party.to(st_config, cond="cond_config_is_active") |
                        st_vacation.to(st_config, cond="cond_config_is_active") |
                        st_boost.to(st_config, cond="cond_config_is_active") |
                        st_off.to(st_config, cond="cond_config_is_active") |
                        st_config.to.itself(cond="cond_config_is_active") |
                        st_config.to(st_off, cond="cond_window_is_open") |
                        st_config.to(st_boost, cond="cond_boost_is_active") |
                        st_config.to(st_vacation, cond="cond_mode_is_vacation") |
                        st_config.to(st_party, cond="cond_party_is_active") |
                        st_config.to(st_manual, cond="cond_mode_is_manual") |
                        st_config.to(st_auto, cond="cond_mode_is_auto") |
                        st_auto.to.itself() |
                        st_boost.to.itself() |
                        st_config.to.itself() |
                        st_manual.to.itself() |
                        st_off.to.itself() |
                        st_party.to.itself() |
                        st_vacation.to.itself())

    tr_mode_change = (st_auto.to(st_manual, cond="cond_mode_is_manual") |
                      st_auto.to(st_vacation, cond="cond_mode_is_vacation") |
                      st_manual.to(st_auto, cond="cond_mode_is_auto") |
                      st_manual.to(st_vacation, cond="cond_mode_is_vacation") |
                      st_vacation.to(st_auto, cond="cond_mode_is_auto") |
                      st_vacation.to(st_manual, cond="cond_mode_is_manual") |
                      st_auto.to.itself() |
                      st_boost.to.itself() |
                      st_config.to.itself() |
                      st_manual.to.itself() |
                      st_off.to.itself() |
                      st_party.to.itself() |
                      st_vacation.to.itself())

    tr_party_change = (st_auto.to(st_party, cond="cond_party_is_active") |
                       st_manual.to(st_party, cond="cond_party_is_active") |
                       st_party.to(st_manual, cond="cond_mode_is_manual") |
                       st_party.to(st_auto, cond="cond_mode_is_auto") |
                       st_auto.to.itself() |
                       st_boost.to.itself() |
                       st_config.to.itself() |
                       st_manual.to.itself() |
                       st_off.to.itself() |
                       st_party.to.itself() |
                       st_vacation.to.itself())

    tr_window_change = (st_auto.to(st_off, cond="cond_window_is_open") |
                        st_manual.to(st_off, cond="cond_window_is_open") |
                        st_party.to(st_off, cond="cond_window_is_open") |
                        st_vacation.to(st_off, cond="cond_window_is_open") |
                        st_boost.to(st_off, cond="cond_window_is_open") |
                        st_off.to(st_config, cond="cond_config_is_active") |
                        st_off.to.itself(cond="cond_window_is_open") |
                        st_off.to(st_boost, cond="cond_boost_is_active") |
                        st_off.to(st_vacation, cond="cond_mode_is_vacation") |
                        st_off.to(st_party, cond="cond_party_is_active") |
                        st_off.to(st_manual, cond="cond_mode_is_manual") |
                        st_off.to(st_auto, cond="cond_mode_is_auto") |
                        st_auto.to.itself() |
                        st_boost.to.itself() |
                        st_config.to.itself() |
                        st_manual.to.itself() |
                        st_off.to.itself() |
                        st_party.to.itself() |
                        st_vacation.to.itself())

    def __init__(self, name="unnamed", logger=None):
        # variables
        self._thermostat_name = name
        self._logger = logger

        self._boost = False
        self._config = False
        self._mode = self.AUTO
        self._party = False
        self._window_open = False

#        for name, value in os.environ.items():
#            self._logger.debug("{0}: {1}".format(name, value))

        super(thermostat_statemachine, self).__init__()

    def get_name(self):
        """return the name of the statemachine
        Returns:
            string: name
        """
        return self._thermostat_name

    def get_state_name(self):
        """return the current state of the statemachine
        Returns:
            string: state name
        """
        return self.current_state.name

    def get_mode(self):
        """return the mode of the thermostat
        Returns:
            string: mode
        """
        return self._mode

    # set internal states BEFORE the event is send
    def set_boost(self, state):
        """set internal state of boost
        Args:
            state (bool): state of boost
        """
        self._boost = state
        self._logger.info(
            self.get_name() + "(" + str(id(self)) + "): - Boost is: " + str(self._boost))

    def set_config(self, state):
        """set internal state of boost
        Args:
            state (bool): state of boost
        """
        self._config = state
        self._logger.info(
            self.get_name() + "(" + str(id(self)) + "): - Config is: " + str(self._config))

    def set_mode(self, state):
        """set internal state of mode (auto/manual/vacation)
        Args:
            state (string): state of boost (see state_map)
        """
        self._mode = state
        self._logger.info(self.get_name() + "(" + str(id(self)) +
                          "): - Mode is: " + str(self._mode))

    def set_party(self, state):
        """set internal state of party
        Args:
            state (bool): state of party
        """
        self._party = state
        self._logger.info(
            self.get_name() + "(" + str(id(self)) + "): - Party is: " + str(self._party))

    def set_window_open(self, state):
        """set internal state of window_open
        Args:
            state (bool): state of window_open
        """
        self._window_open = state
        self._logger.info(self.get_name() +
                          ": - WindowOpen is: " + str(self._window_open))

    # Conditions
    def cond_boost_is_active(self):
        """check if boost mode is active
        Returns:
            boolean: True/False
        """
        self._logger.debug(self.get_name() + "(" + str(id(self)) +
                           "): boost = '" + str(self._boost) + "'.")
        return self._boost

    def cond_config_is_active(self):
        """check if config mode is active
        Returns:
            boolean: True/False
        """
        self._logger.debug(self.get_name() + "(" + str(id(self)) +
                           "): config = '" + str(self._config) + "'.")
        return self._config

    def cond_mode_is_auto(self):
        """check if auto mode is active
        Returns:
            boolean: True/False
        """
        self._logger.debug(
            self.get_name() + "(" + str(id(self)) + "): mode = '" + str(self._mode) + "'.")
        return self._mode == self.AUTO

    def cond_mode_is_manual(self):
        """check if manual mode is active
        Returns:
            boolean: True/False
        """
        self._logger.debug(
            self.get_name() + "(" + str(id(self)) + "): mode = '" + str(self._mode) + "'.")
        return self._mode == self.MANUAL

    def cond_mode_is_vacation(self):
        """check if vacation mode is active
        Returns:
            boolean: True/False
        """
        self._logger.debug(
            self.get_name() + "(" + str(id(self)) + "): mode = '" + str(self._mode) + "'.")
        return self._mode == self.VACATION

    def cond_party_is_active(self):
        """check if party mode is active
        Returns:
            boolean: True/False
        """
        self._logger.debug(self.get_name() + "(" + str(id(self)) +
                           "): party = '{}'.".format(str(self._party)))
        return self._party

    def cond_window_is_open(self):
        """check if window is open
        Returns:
            boolean: True/False
        """
        self._logger.debug(self.get_name() + "(" + str(id(self)) +
                           "): window_open = '{}'.".format(str(self._window_open)))
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
        self._logger.info(
            self.get_name() + "(" + str(id(self)) + "): is in state {}.".format(state.id))
