import sys
import os

# log:set INFO jsr223.jython.Thermostat_statemachines_create

OH_CONF = os.getenv('OPENHAB_CONF')

sys.path.append(os.path.join(OH_CONF, "automation/lib/python/personal"))
from statemachine import State, StateMachine


class ThermostatStateMachine(StateMachine):
    "handle state of thermostats"

    # constants
    AUTO = "auto"
    MANUAL = "manual"
    VACATION = "vacation"

    # States
    st_auto = State("Auto", initial=True)
    st_boost = State("Boost")
    st_config = State("Config")
    st_manual = State("Manual")
    st_off = State("Off")
    st_party = State("Party")
    st_vacation = State("Vacation")

    # Transitions
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

    tr_boost_change = (st_auto.to(st_boost, cond="cond_boost_is_active") |
                       st_manual.to(st_boost, cond="cond_boost_is_active") |
                       st_party.to(st_boost, cond="cond_boost_is_active") |
                       st_vacation.to(st_boost, cond="cond_boost_is_active") |
                       st_boost.to(st_config, unless="cond_config_is_active") |
                       st_boost.to(st_off, unless="cond_window_is_open") |
                       st_boost.to.itself(cond="cond_boost_is_active") |
                       st_boost.to(st_vacation, unless="cond_mode_is_vacation") |
                       st_boost.to(st_party, unless="cond_party_is_active") |
                       st_boost.to(st_auto, unless="cond_mode_is_auto") |
                       st_boost.to.itself(unless="cond_mode_is_manual") |
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

    tr_mode_change = (st_vacation.to(st_auto, cond="cond_mode_is_auto") |
                      st_manual.to(st_auto, cond="cond_mode_is_auto") |
                      st_auto.to(st_manual, cond="cond_mode_is_manual") |
                      st_vacation.to(st_manual, cond="cond_mode_is_manual") |
                      st_auto.to(st_vacation, cond="cond_mode_is_vacation") |
                      st_manual.to(st_vacation, cond="cond_mode_is_vacation") |
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

        for name, value in os.environ.items():
            self._logger.debug("{0}: {1}".format(name, value))

        super(ThermostatStateMachine, self).__init__()

    def get_name(self):
        """return the name of the statemachine
        Returns:
            string: name
        """
        return self._thermostat_name

    # set internal states BEFORE the event is send
    def set_boost(self, state):
        """set internal state of boost
        Args:
            state (bool): state of boost
        """
        self._boost = state
        self._logger.info(self.get_name() + " - Boost is: " + str(self._boost))

    def set_config(self, state):
        """set internal state of boost
        Args:
            state (bool): state of boost
        """
        self._config = state
        self._logger.info(self.get_name() +
                          " - Config is: " + str(self._config))

    def set_mode(self, state):
        """set internal state of mode (auto/manual/vacation)
        Args:
            state (bool): state of boost
        """
        self._mode = state
        self._logger.info(self.get_name() + " - Mode is: " + str(self._mode))

    def set_party(self, state):
        """set internal state of party
        Args:
            state (bool): state of party
        """
        self._party = state
        self._logger.info(self.get_name() + " - Party is: " + str(self._party))

    def set_window_open(self, state):
        """set internal state of window_open
        Args:
            state (bool): state of window_open
        """
        self._window_open = state
        self._logger.info(
            self.get_name() + " - WindowOpen is: " + str(self._window_open))

    # Conditions
    def cond_boost_is_active(self):
        """check if boost mode is active
        Returns:
            boolean: True/False
        """
        return self._boost

    def cond_config_is_active(self):
        """check if config mode is active
        Returns:
            boolean: True/False
        """
        return self._config

    def cond_mode_is_auto(self):
        """check if auto mode is active
        Returns:
            boolean: True/False
        """
        return self._mode == self.AUTO

    def cond_mode_is_manual(self):
        """check if manual mode is active
        Returns:
            boolean: True/False
        """
        return self._mode == self.MANUAL

    def cond_mode_is_vacation(self):
        """check if vacation mode is active
        Returns:
            boolean: True/False
        """
        return self._mode == self.VACATION

    def cond_party_is_active(self):
        """check if party mode is active
        Returns:
            boolean: True/False
        """
        return self._party

    def cond_window_is_open(self):
        """check if window is open
        Returns:
            boolean: True/False
        """
        return self._window_open

    # see https://python-statemachine.readthedocs.io/en/latest/actions.html#ordering
    def before_transition(self, event, state):
        """events received for any state """
        self._logger.debug(self._thermostat_name +
                           ": Before   '{}' on the '{}' state.".format(event, state.id))

    def on_enter_state(self, event, state):
        """entry function for any state """
        self._logger.debug(self._thermostat_name +
                           ": Entering '{}' state from '{}' event.".format(state.id, event))
