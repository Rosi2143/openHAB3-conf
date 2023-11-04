"""StateMachine for Indego operation states """
import os
import platform
from datetime import datetime, timedelta

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
        os.path.join(imagepath, state_machine.get_name() + "_indego_sm.png")
    )


def get_internal_state_machine_state(state_machine):
    """log internal states
    Args:
        sm (string): statemachine where info is wanted
    Returns:
        string: internal info for all states
    """
    info = "Internal machine states (" + str(state_machine.get_name()) + "):"
    info += "\n   state           = " + str(state_machine.get_state_name())
    info += "\n   _reportedState  = " + str(state_machine.get_reported_state())
    info += "\n   _operationState = " + str(state_machine.get_operation_state())
    return info


class IndegoStatemachine(StateMachine):
    "handle operation states of Indego"

    # error keys
    STATUS_MOW = "mow"
    STATUS_MOWING_COMPLETE = "mowing_complete"
    STATUS_PAUSE = "pause"
    STATUS_DOCK = "dock"
    STATUS_UNKNOWN = "unknown"

    # States
    init = State(STATUS_UNKNOWN, initial=True)
    mow = State(STATUS_MOW)
    mowing_complete = State(STATUS_MOWING_COMPLETE)
    pause = State(STATUS_PAUSE)
    dock = State(STATUS_DOCK)

    # Transitions
    # mowing state
    tr_border_cut = (
        init.to(mow)
        | mow.to.itself(internal=True)
        | mowing_complete.to(mow)
        | pause.to(mow)
        | dock.to(mow)
    )

    tr_leaving_dock = (
        init.to(mow)
        | mow.to.itself(internal=True)
        | mowing_complete.to(mow)
        | pause.to(mow)
        | dock.to(mow)
    )

    tr_mowing = (
        init.to(mow)
        | mow.to.itself(internal=True)
        | mowing_complete.to(mow)
        | pause.to(mow)
        | dock.to(mow)
    )

    tr_spotmow = (
        init.to(mow)
        | mow.to.itself(internal=True)
        | mowing_complete.to(mow)
        | pause.to(mow)
        | dock.to(mow)
    )

    # mowing_complete state
    tr_mowing_complete = (
        init.to(mowing_complete)
        | mow.to(mowing_complete)
        | mowing_complete.to.itself(internal=True)
        | pause.to(mowing_complete)
        | dock.to(mowing_complete)
    )

    # pause state
    tr_battery_low = (
        init.to(pause)
        | mow.to(pause)
        | mowing_complete.to(pause)
        | pause.to.itself(internal=True)
        | dock.to(pause)
    )

    tr_idle = (
        init.to(pause)
        | mow.to(pause)
        | mowing_complete.to(pause)
        | pause.to.itself(internal=True)
        | dock.to(pause)
    )

    tr_paused = (
        init.to(pause)
        | mow.to(pause)
        | mowing_complete.to(pause)
        | pause.to.itself(internal=True)
        | dock.to(pause)
    )

    tr_relocalising = (
        init.to(pause)
        | mow.to(pause)
        | mowing_complete.to(pause)
        | pause.to.itself(internal=True)
        | dock.to(pause)
    )

    tr_returning = (
        init.to(pause)
        | mow.to(pause)
        | mowing_complete.to(pause)
        | pause.to.itself(internal=True)
        | dock.to(pause)
    )

    # docking state
    tr_charging = (
        init.to(dock)
        | mow.to(dock)
        | mowing_complete.to(dock)
        | pause.to(dock)
        | dock.to.itself(internal=True)
    )

    tr_docked = (
        init.to(dock)
        | mow.to(dock)
        | mowing_complete.to(dock)
        | pause.to.itself(internal=True)  # pause to dock due to battery low
        | dock.to.itself(internal=True)
    )

    def __init__(self, name="unnamed", logger=None):
        # variables
        self._indego_name = name
        self._logger = logger

        self._reported_state = self.STATUS_UNKNOWN
        self._operationState = self.STATUS_UNKNOWN

        self._start_time_mow = datetime.now()
        self._mowing_time = timedelta(0)
        self._start_time_pause = datetime.now()
        self._pause_time = timedelta(0)

        self._time_state_entered = datetime.now()

        super(IndegoStatemachine, self).__init__()

        get_state_machine_graph(self)

    def format_time(self, in_time):
        return str(in_time).split(".")[0]

    def get_name(self):
        """return the name of the statemachine
        Returns:
            string: name
        """
        return self._indego_name

    def get_mow_start_time(self):
        """return the time the indego started last mowing
        Returns:
            string: name
        """
        return self._start_time_mow

    def get_mow_duration(self):
        """return the time the indego spend mowing
        Returns:
            string: name
        """
        return self._mowing_time

    def get_pause_start_time(self):
        """return the time the indego started last pause
        Returns:
            string: name
        """
        return self._start_time_pause

    def get_pause_duration(self):
        """return the name of the statemachine
        Returns:
            string: name
        """
        return self._pause_time

    def get_reported_state(self):
        """return the state reported by OH
        Returns:
            string: state reported
        """
        return self._reported_state

    def get_operation_state(self):
        """return the operational state of the indego
        Returns:
            string: operational state
        """
        return self._operationState

    # set internal states BEFORE the event is send
    def set_reported_state(self, reported_state):
        """set reported state
        Args:
            state (string): reported state of indego
        """
        self._reported_state = reported_state
        self._logger.info(
            self.get_name()
            + "("
            + str(id(self))
            + "): - reported state is: "
            + str(self._reported_state)
        )
        if "Battery low" in reported_state:
            self.send("tr_battery_low")
        elif "Border cut" in reported_state:
            self.send("tr_border_cut")
        elif "Charging" in reported_state:
            self.send("tr_charging")
        elif "Complete" in reported_state:
            self.send("tr_mowing_complete")
        elif "Docked" in reported_state:
            self.send("tr_docked")
        elif "Idle" in reported_state:
            self.send("tr_idle")
        elif "Init" in reported_state:
            # don't do anything
            pass
        elif "Lawn complete" in reported_state:
            self.send("tr_mowing_complete")
        elif "Leaving" in reported_state:
            self.send("leaving_dock")
        elif "Mowing" in reported_state:
            self.send("tr_mowing")
        elif "Paused" in reported_state:
            self.send("tr_paused")
        elif "Relocalising" in reported_state:
            self.send("tr_relocalising")
        elif "Returning to Dock" == reported_state:
            self.send("tr_mowing_complete")
        elif "Returning" in reported_state:
            self.send("tr_returning")
        elif "SpotMow" in reported_state:
            self.send("tr_spotmow")
        else:
            self._logger.error("Unknown state %s", reported_state)

    # Conditions
    def cond_is_operational_state_dock(self):
        """rule to decide if current operational state is "dock"
        Returns:
            boolean: True/False
        """
        self._logger.debug(
            self.get_name() + "(" + str(id(self)) + "): cond_is_operational_state_dock"
        )

        return self.get_operation_state() == self.STATUS_DOCK

    def cond_is_operational_state_mow(self):
        """rule to decide if current operational state is "mow"
        Returns:
            boolean: True/False
        """
        self._logger.debug(
            self.get_name() + "(" + str(id(self)) + "): cond_is_operational_state_mow"
        )

        return self.get_operation_state() == self.STATUS_MOW

    def cond_is_operational_state_mowing_complete(self):
        """rule to decide if current operational state is "mowing complete"
        Returns:
            boolean: True/False
        """
        self._logger.debug(
            self.get_name()
            + "("
            + str(id(self))
            + "): cond_is_operational_state_mowing_complete"
        )

        return self.get_operation_state() == self.STATUS_MOWING_COMPLETE

    def cond_is_operational_state_pause(self):
        """rule to decide if current operational state is "pause"
        Returns:
            boolean: True/False
        """
        self._logger.debug(
            self.get_name() + "(" + str(id(self)) + "): cond_is_operational_state_pause"
        )

        return self.get_operation_state() == self.STATUS_PAUSE

    # see https://python-statemachine.readthedocs.io/en/latest/actions.html#ordering
    def before_transition(self, event, state):
        """events received for any state"""
        self._logger.debug(
            f"{self.get_name()} ({str(id(self))}): \
Before   '{event}' in '{state.id}' state."
        )
        self._logger.info(
            f"time spend in state {state.id} = {self.format_time(datetime.now() -self._time_state_entered)}"
        )

    def on_enter_dock(self, source):
        self._logger.debug(
            f"{self.get_name()}({str(id(self))}): entered {self.STATUS_DOCK} - source state was {source.id}"
        )
        if source.id == self.STATUS_MOWING_COMPLETE:
            self._pause_time = self._pause_time + (
                datetime.now() - self.get_pause_start_time()
            )
            self._mowing_time = (
                datetime.now() - self.get_mow_start_time() - self.get_pause_duration()
            )
            self._logger.info("###########################################")
            self._logger.info("Mowing complete")
            self._logger.info(
                "overall time = %s",
                self.format_time(datetime.now() - self.get_mow_start_time()),
            )
            self._logger.info(
                "Mowing time  = %s", self.format_time(self.get_mow_duration())
            )
            self._logger.info(
                "Pause time   = %s", self.format_time(self.get_pause_duration())
            )
            self._logger.info("###########################################")

            self._start_time_pause = datetime.min
            self._pause_time = timedelta(0)
            self._start_time_mow = datetime.min
        else:
            self._logger.error("Undefined transition")

    def on_enter_mow(self, source):
        self._logger.debug(
            f"{self.get_name()}({str(id(self))}): \
entered {self.STATUS_MOW} - source state was {source.id}"
        )

        if (source.id == self.STATUS_DOCK) or (
            source.id == self.STATUS_MOWING_COMPLETE
        ):
            self._start_time_mow = datetime.now()
            self._mowing_time = timedelta(0)
            self._logger.info(f"{self.get_name()}({str(id(self))}): starting mow timer")
        elif (source.id == self.STATUS_PAUSE) or (
            source.id == self.STATUS_MOWING_COMPLETE
        ):
            self._pause_time = self._pause_time + (
                datetime.now() - self.get_pause_start_time()
            )
            self._start_time_pause = datetime.min
            self._logger.info(
                f"{self.get_name()}({str(id(self))}): stopping pause timer"
            )
        else:
            self._logger.info(
                f"{self.get_name()}({str(id(self))}): no action defined for {source.id}"
            )

    def on_enter_mowing_complete(self, source):
        self._logger.debug(
            f"{self.get_name()}({str(id(self))}): entered {self.STATUS_DOCK} - source state was {source.id}"
        )
        if source.id == self.STATUS_MOW:
            self._start_time_pause = datetime.now()
            self._logger.debug(
                f"{self.get_name()}({str(id(self))}): starting pause timer"
            )
        else:
            self._logger.error("Undefined transition")

    def on_enter_pause(self, source):
        self._logger.debug(
            f"{self.get_name()}({str(id(self))}): entered {self.STATUS_PAUSE} - source state was {source.id}"
        )
        if (source.id == self.STATUS_MOW) or (source.id == self.STATUS_MOWING_COMPLETE):
            self._start_time_pause = datetime.now()
            self._logger.debug(
                f"{self.get_name()}({str(id(self))}): starting pause timer"
            )
        else:
            self._logger.error("Undefined transition")

    def after_transition(self, event, state):
        """last function in state change queue"""
        self._logger.info(f"{self.get_name()}({str(id(self))}): is in state {state.id}")
        self._time_state_entered = datetime.now()

    def get_action_timer(self):
        if self.current_state.name.lower() == self.STATUS_DOCK:
            return self.get_mow_duration(), self.get_pause_duration()
        else:
            if self.get_pause_start_time() != datetime.min:
                pausetime = self.get_pause_duration() + (
                    datetime.now() - self.get_pause_start_time()
                )
            else:
                pausetime = self.get_pause_duration()
            mowtime = (datetime.now() - self.get_mow_start_time()) - pausetime

            return mowtime, pausetime
