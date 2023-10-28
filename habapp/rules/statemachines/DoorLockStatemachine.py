"""StateMachine for Homematic-IP DoorLock """
import os
import platform

# log:set INFO jsr223.jython.Thermostat_statemachines_create

OH_CONF = "/etc/openhab/"  # os.getenv('OPENHAB_CONF')
scriptpath = os.path.join(OH_CONF, "habapp")

from statemachine import State, StateMachine
from statemachine.contrib.diagram import DotGraphMachine


def get_state_machine_graph(state_machine):
    """create the PNG of the statemachine
    Args:
        sm_name (string): instance of the statemachine
    Returns:
        None
    """
    if platform.system() == "Windows":
        return

    # also accepts instances
    graph = DotGraphMachine(state_machine)
    imagepath = os.path.join(scriptpath, "images")
    if not os.path.exists(imagepath):
        os.makedirs(imagepath)
    graph().write_png(
        os.path.join(imagepath, state_machine.get_name() + "_doorlock_sm.png")
    )


def get_internal_state_machine_state(state_machine):
    """log internal states
    Args:
        sm (string): statemachine where info is wanted
    Returns:
        string: internal info for all states
    """
    info = "Internal machine states (" + str(state_machine.get_name()) + "):"
    info += "\n   state          = " + str(state_machine.get_state_name())
    info += "\n   _lock_error    = " + str(state_machine.get_lock_error())
    info += "\n   lock_error     = " + str(state_machine.get_lock_error_dict())
    info += "\n   _light         = " + str(state_machine.get_light())
    info += "\n   _presence      = " + str(state_machine.get_presence())
    info += "\n   _dark_outside  = " + str(state_machine.get_dark_outside())
    info += "\n   _door_open     = " + str(state_machine.get_door_open())
    info += "\n   _reported_lock = " + str(state_machine.get_reported_lock())
    return info


class DoorLockStatemachine(StateMachine):
    "handle state of DoorLock"

    # error keys
    JAMMED = "jammed"
    CONFIG_PENDING = "config_pending"
    UNREACHABLE = "unreachable"
    error_keys = [JAMMED, CONFIG_PENDING, UNREACHABLE]

    LOCKED = "LOCKED"
    UNLOCKED = "UNLOCKED"
    state_map = {LOCKED: True, UNLOCKED: False}

    # States
    st_unlocked = State("unlocked", initial=True)
    st_locked = State("locked")
    st_error = State("error")

    # Transitions
    tr_dark_outside_change = (
        st_unlocked.to(st_error, cond="cond_error")
        | st_unlocked.to(st_locked, cond="cond_lock_required")
        | st_unlocked.to.itself()
        | st_locked.to(st_error, cond="cond_error")
        |
        # st_locked.to(st_unlocked, unless="cond_lock_required") |
        st_locked.to.itself()
        | st_error.to(st_unlocked, unless=["cond_error", "cond_lock_required"])
        |
        # st_error.to(st_locked, unless="cond_error",
        #             cond="cond_lock_required") |
        st_error.to.itself()
    )

    tr_door_open_change = (
        st_unlocked.to(st_error, cond="cond_error")
        | st_unlocked.to(st_locked, cond="cond_lock_required")
        | st_unlocked.to.itself()
        | st_locked.to(st_error, cond="cond_error")
        | st_locked.to(st_unlocked, unless="cond_lock_required")
        | st_locked.to.itself()
        | st_error.to(st_unlocked, unless=["cond_error", "cond_lock_required"])
        | st_error.to(st_locked, unless="cond_error", cond="cond_lock_required")
        | st_error.to.itself()
    )

    tr_error_change = (
        st_unlocked.to(st_error, cond="cond_error")
        | st_unlocked.to.itself()
        | st_locked.to(st_error, cond="cond_error")
        | st_locked.to.itself()
        | st_error.to.itself(cond="cond_error")
        | st_error.to(st_locked, cond="cond_lock_required")
        | st_error.to(st_unlocked, unless="cond_lock_required")
    )

    tr_light_change = (
        st_unlocked.to(st_error, cond="cond_error")
        | st_unlocked.to(st_locked, cond="cond_lock_required")
        | st_unlocked.to.itself()
        | st_locked.to(st_error, cond="cond_error")
        | st_locked.to(st_unlocked, unless="cond_lock_required")
        | st_locked.to.itself()
        | st_error.to(st_unlocked, unless=["cond_error", "cond_lock_required"])
        | st_error.to(st_locked, unless="cond_error", cond="cond_lock_required")
        | st_error.to.itself()
    )

    tr_presence_change = (
        st_unlocked.to(st_error, cond="cond_error")
        | st_unlocked.to(st_locked, cond="cond_lock_required")
        | st_unlocked.to.itself()
        | st_locked.to(st_error, cond="cond_error")
        |
        # st_locked.to(st_unlocked, unless="cond_lock_required") |
        st_locked.to.itself()
        | st_error.to(st_unlocked, unless=["cond_error", "cond_lock_required"])
        | st_error.to(st_locked, unless="cond_error", cond="cond_lock_required")
        | st_error.to.itself()
    )

    tr_reported_lock_change = (
        st_unlocked.to(st_error, cond="cond_error")
        | st_unlocked.to(st_locked, cond="cond_reported_lock")
        | st_unlocked.to.itself()
        | st_locked.to(st_error, cond="cond_error")
        | st_locked.to(st_unlocked, unless="cond_reported_lock")
        | st_locked.to.itself()
        | st_error.to.itself(cond="cond_error")
        | st_error.to(st_locked, cond="cond_lock_required")
        | st_error.to(st_unlocked, unless="cond_lock_required")
    )

    def __init__(self, name="unnamed", logger=None):
        # variables
        self._doorlock_name = name
        self._logger = logger

        self._lock_error = {}
        self._dark_outside = False
        self._door_open = False
        self._reported_lock = False
        self._light = False
        self._presence = True

        #        for name, value in os.environ.items():
        #            self._logger.debug("{0}: {1}".format(name, value))

        super(DoorLockStatemachine, self).__init__()

        get_state_machine_graph(self)

    def get_dark_outside(self):
        """return the state of the dark_outside
        Returns:
            bool: dark_outside state
        """
        return self._dark_outside

    def get_door_open(self):
        """return the state of the door_open
        Returns:
            bool: door_open state
        """
        return self._door_open

    def get_light(self):
        """return the state of the light
        Returns:
            bool: light state
        """
        return self._light

    def get_lock_error(self):
        """return the state of the lock_error
        Returns:
            bool: lock_error state
        """
        if not self._lock_error:
            return False

        return True in self._lock_error.values()

    def get_lock_error_dict(self):
        """return the state of the lock_error
        Returns:
            dict: lock_error dictionary with bool for each state
        """
        return self._lock_error

    def get_name(self):
        """return the name of the statemachine
        Returns:
            string: name
        """
        return self._doorlock_name

    def get_state_name(self):
        """return the current state of the statemachine
        Returns:
            string: state name
        """
        return self.current_state.name

    def get_presence(self):
        """return the state of the presence
        Returns:
            bool: presence state
        """
        return self._presence

    def get_reported_lock(self):
        """return the state of reported lock state
        Returns:
            bool: door_open state
        """
        return self._reported_lock

    # set internal states BEFORE the event is send
    def set_dark_outside(self, state):
        """set internal state of dark_outside
        Args:
            state (bool): state of dark_outside
        """
        self._dark_outside = state
        self._logger.info(
            self.get_name()
            + "("
            + str(id(self))
            + "): - Dark_Outside is: "
            + str(self._dark_outside)
        )

    def set_door_open(self, state):
        """set internal state of door_open
        Args:
            state (bool): state of door_open
        """
        self._door_open = state
        self._logger.info(self.get_name() + ": - DoorOpen is: " + str(self._door_open))

    def set_light(self, state):
        """set internal state of light
        Args:
            state (bool): state of light
        """
        self._light = state
        self._logger.info(
            self.get_name() + "(" + str(id(self)) + "): - Light is: " + str(self._light)
        )

    def set_lock_error(self, key, state):
        """set internal state of lock_error
        Args:
            state (bool): state of lock_error
        """
        if key in self.error_keys:
            self._lock_error[key] = state
            self._logger.info(
                self.get_name()
                + "("
                + str(id(self))
                + "): - Error is: "
                + str(self._lock_error)
            )
        else:
            self._logger.error(
                self.get_name() + "(" + str(id(self)) + "): - undefined key " + key
            )

    def set_presence(self, state):
        """set internal state of presence
        Args:
            state (bool): state of presence
        """
        self._presence = state
        self._logger.info(
            self.get_name()
            + "("
            + str(id(self))
            + "): - Presence is: "
            + str(self._presence)
        )

    def set_reported_lock(self, state):
        """set internal state of reported lock state
        Args:
            state (bool): reported state of lock
        """
        if state not in self.state_map.keys():
            self._logger.error(
                f"{self.get_name()}: - reported LockState invalid: {str(state)}\n \
{str(self.state_map)}"
            )
        else:
            self._reported_lock = self.state_map[state]
            self._logger.info(
                self.get_name()
                + ": - reported LockState is: "
                + str(self._reported_lock)
            )

    # Conditions
    def cond_dark_outside(self):
        """check if it is dark outside
        Returns:
            boolean: True/False
        """
        self._logger.debug(
            f"{self.get_name()} ({str(id(self))}): \
dark_outside = {str(self._dark_outside)}"
        )
        return self._dark_outside

    def cond_door_is_open(self):
        """check if door is open
        Returns:
            boolean: True/False
        """
        self._logger.debug(
            f"{self.get_name()} ({str(id(self))}): \
door_open = {str(self._door_open)}"
        )
        return self._door_open

    def cond_error(self):
        """rule to decide if the lock is in an "error" state
        Returns:
            boolean: True/False
        """
        self._logger.debug(self.get_name() + "(" + str(id(self)) + "): cond_error")

        result = False
        if self.get_lock_error():
            result = True
        elif self.cond_lock_required():
            if self._door_open:
                result = True
        elif self._door_open:
            if self._reported_lock:
                result = True

        self._logger.debug(
            self.get_name()
            + "("
            + str(id(self))
            + "): result (cond_error) = "
            + str(result)
        )

        return result

    def cond_reported_lock(self):
        """check if reported lock is active
        Returns:
            boolean: True/False
        """
        self._logger.debug(
            self.get_name()
            + "("
            + str(id(self))
            + "): ExternalLock = '"
            + str(self._reported_lock)
            + "'."
        )
        return self._reported_lock

    def cond_light_is_active(self):
        """check if light mode is active
        Returns:
            boolean: True/False
        """
        self._logger.debug(
            self.get_name()
            + "("
            + str(id(self))
            + "): light = '"
            + str(self._light)
            + "'."
        )
        return self._light

    def cond_lock_required(self):
        """rule to decide if the door shall be locked
        Returns:
            boolean: True/False
        """
        self._logger.debug(
            self.get_name() + "(" + str(id(self)) + "): cond_lock_required"
        )
        self._logger.debug(get_internal_state_machine_state(self))

        result = False

        if self._door_open:
            result = False
        elif (not self._presence) and (not self._light) and self._dark_outside:
            result = True
        elif self._dark_outside:
            if not self._light:
                result = True

        self._logger.debug(
            self.get_name()
            + "("
            + str(id(self))
            + "): result (cond_lock_required) = "
            + str(result)
        )

        return result

    def cond_lock_error_is_active(self):
        """check if lock_error mode is active
        Returns:
            boolean: True/False
        """
        self._logger.debug(
            self.get_name()
            + "("
            + str(id(self))
            + "): lock_error = '"
            + str(self._lock_error)
            + "'."
        )
        return self._lock_error

    def cond_presence_is_active(self):
        """check if presence mode is active
        Returns:
            boolean: True/False
        """
        self._logger.debug(
            self.get_name()
            + "("
            + str(id(self))
            + "): presence = '"
            + str(self._presence)
            + "'."
        )
        return self._presence

    # see https://python-statemachine.readthedocs.io/en/latest/actions.html#ordering
    def before_transition(self, event, state):
        """events received for any state"""
        self._logger.debug(
            f"{self.get_name()} ({str(id(self))}): \
Before   '{event}' in '{state.id}' state."
        )

    def on_enter_state(self, event, state):
        """entry function for any state"""
        self._logger.debug(
            f"{self.get_name()} ({str(id(self))}): \
Entering '{state.id}' state triggered by '{event}' event."
        )

    def after_transition(self, event, state):
        """last function in state change queue"""
        self._logger.info(
            f"{self.get_name()} ({str(id(self))}): \
is in state {state.id}"
        )
