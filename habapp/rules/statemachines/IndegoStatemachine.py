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
        | mow.to.itself(internal=False)
        | mowing_complete.to(mow)
        | pause.to(mow)
        | dock.to(mow)
    )

    tr_leaving_dock = (
        init.to(mow)
        | mow.to.itself(internal=False)
        | mowing_complete.to(mow)
        | pause.to(mow)
        | dock.to(mow)
    )

    tr_mowing = (
        init.to(mow)
        | mow.to.itself(internal=False)
        | mowing_complete.to(mow)
        | pause.to(mow)
        | dock.to(mow)
    )

    tr_spotmow = (
        init.to(mow)
        | mow.to.itself(internal=False)
        | mowing_complete.to(mow)
        | pause.to(mow)
        | dock.to(mow)
    )

    # mowing_complete state
    tr_mowing_complete = (
        init.to(mowing_complete)
        | mow.to(mowing_complete)
        | mowing_complete.to.itself(internal=False)
        | pause.to(mowing_complete)
        | dock.to(mowing_complete)
    )

    # pause state
    tr_battery_low = (
        init.to(pause)
        | mow.to(pause)
        | mowing_complete.to(pause)
        | pause.to.itself(internal=False)
        | dock.to(pause)
    )

    tr_idle = (
        init.to(pause)
        | mow.to(pause)
        | mowing_complete.to(pause)
        | pause.to.itself(internal=False)
        | dock.to(pause)
    )

    tr_paused = (
        init.to(pause)
        | mow.to(pause)
        | mowing_complete.to(pause)
        | pause.to.itself(internal=False)
        | dock.to(pause)
    )

    tr_relocalising = (
        init.to(pause)
        | mow.to(pause)
        | mowing_complete.to(pause)
        | pause.to.itself(internal=False)
        | dock.to(pause)
    )

    tr_returning = (
        init.to(pause)
        | mow.to(pause)
        | mowing_complete.to(pause)
        | pause.to.itself(internal=False)
        | dock.to(pause)
    )

    # docking state
    tr_charging = (
        init.to(dock)
        | mow.to(dock)
        | mowing_complete.to(dock)
        | pause.to(dock)
        | dock.to.itself(internal=False)
    )

    tr_docked = (
        init.to(dock)
        | mow.to(dock)
        | mowing_complete.to(dock)
        | pause.to.itself(internal=False)  # pause to dock due to battery low
        | dock.to.itself(internal=False)
    )

    def __init__(self, name="unnamed", logger=None):
        # variables
        self._indego_name = name
        self._logger = logger

        self._reported_state = self.STATUS_UNKNOWN

        self._time_state_entered = datetime.now()
        self.start_mowing()

        super(IndegoStatemachine, self).__init__()

        get_state_machine_graph(self)

    def get_trace_header(self):
        return self.get_name() + "(" + str(id(self)) + "): - "

    def format_time(self, in_time) -> str:
        return str(in_time).split(".")[0]

    def get_name(self) -> str:
        """return the name of the statemachine
        Returns:
            string: name
        """
        return self._indego_name

    # #########
    # mowing
    # #########
    def get_total_time(self) -> datetime:
        """return the total time the indego spend in the current state
        Returns:
            string: name
        """
        return datetime.now() - self.get_mow_start_time()

    def start_mowing(self) -> None:
        """set the start time of the mowing"""
        self._start_time_mow = datetime.now()
        self._mowing_duration_sec = 0

    def get_mow_start_time(self) -> datetime:
        """return the time the indego started last mowing
        Returns:
            string: name
        """
        return self._start_time_mow

    def pause_mowing(self, last_state: str) -> None:
        self._logger.info(
            "Last Mow time  = %s",
            self.format_time(self.get_current_mow_duration_sec(last_state)),
        )
        self._mowing_duration_sec += self.get_new_mowing_duration_sec(
            last_state
        ) - self.get_pause_duration_sec(last_state)
        self._logger.info(
            "Current Total Mow time  = %s",
            self.format_time(self.get_current_mow_duration_sec(last_state)),
        )

    def resume_mowing(self, new_state: str) -> None:
        self._logger.info(
            "Last Mow time  = %s",
            self.format_time(self.get_current_mow_duration_sec(new_state)),
        )

    def stop_mowing(self, last_state: str) -> None:
        self._logger.info(
            "Total Mow time  = %s",
            self.format_time(self.get_total_mow_duration_sec(last_state)),
        )
        self._start_time_mow = datetime.min

    def get_total_mow_duration_sec(self, state: str) -> int:
        """return the time the indego spend mowing
        Returns:
            string: name
        """
        return self.get_current_mow_duration_sec(
            state
        ) + self.get_new_mowing_duration_sec(state)

    def get_current_mow_duration_sec(self, state: str) -> int:
        """return the time the indego spend in the current mowing state
        Returns:
            string: name
        """
        if state == self.STATUS_MOW:
            return int(self._mowing_duration_sec)
        else:
            return 0

    def get_new_mowing_duration_sec(self, state: str) -> int:
        """return the time the indego spend in the current mowing state"""
        if state == self.STATUS_MOW:
            return int(self.get_time_in_state())
        else:
            return 0

    # #########
    # pause
    # #########
    def get_pause_duration_sec(self, state: str) -> int:
        """return the name of the statemachine
        Returns:
            string: name
        """
        return int(
            self.get_total_time().total_seconds()
            - self.get_total_mow_duration_sec(state)
        )

    def get_new_pause_duration_sec(self, state: str) -> int:
        """return the time the indego spend in the current pause"""
        if state == self.STATUS_PAUSE:
            return int(self.get_time_in_state())
        else:
            return 0

    # #########
    # states
    # #########
    def get_reported_state(self) -> str:
        """return the state reported by OH
        Returns:
            string: state reported
        """
        return self._reported_state

    def get_state_name(self) -> str:
        """return the operational state of the indego
        Returns:
            string: operational state
        """
        return self.current_state.name

    def get_time_in_state(self) -> int:
        """return the time the indego spend in the current state
        Returns:
            string: name
        """
        return int((datetime.now() - self._time_state_entered).total_seconds())

    # set internal states BEFORE the event is send
    def set_reported_state(self, reported_state) -> None:
        """set reported state
        Args:
            state (string): reported state of indego
        """
        self._reported_state = reported_state
        self._logger.info(
            self.get_trace_header() + "reported state is: " + str(self._reported_state)
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
            self.send("tr_leaving_dock")
        elif "Mowing" in reported_state:
            self.send("tr_mowing")
        elif "Paused" in reported_state:
            self.send("tr_paused")
        elif "Relocalising" in reported_state:
            self.send("tr_relocalising")
        elif "Returning" in reported_state:
            self.send("tr_returning")
        elif "SpotMow" in reported_state:
            self.send("tr_spotmow")
        else:
            self._logger.error(
                "%sUnknown state %s reported", self.get_trace_header(), reported_state
            )

    # Conditions
    def cond_is_operational_state_dock(self) -> bool:
        """rule to decide if current operational state is "dock"
        Returns:
            boolean: True/False
        """
        self._logger.debug(self.get_trace_header() + "cond_is_operational_state_dock")

        return self.get_state_name() == self.STATUS_DOCK

    def cond_is_operational_state_mow(self) -> bool:
        """rule to decide if current operational state is "mow"
        Returns:
            boolean: True/False
        """
        self._logger.debug(self.get_trace_header() + "cond_is_operational_state_mow")

        return self.get_state_name() == self.STATUS_MOW

    def cond_is_operational_state_mowing_complete(self) -> bool:
        """rule to decide if current operational state is "mowing complete"
        Returns:
            boolean: True/False
        """
        self._logger.debug(
            self.get_trace_header() + "cond_is_operational_state_mowing_complete"
        )

        return self.get_state_name() == self.STATUS_MOWING_COMPLETE

    def cond_is_operational_state_pause(self) -> bool:
        """rule to decide if current operational state is "pause"
        Returns:
            boolean: True/False
        """
        self._logger.debug(self.get_trace_header() + "cond_is_operational_state_pause")

        return self.get_state_name() == self.STATUS_PAUSE

    # see https://python-statemachine.readthedocs.io/en/latest/actions.html#ordering
    # #################
    # transition start
    # #################
    def before_transition(self, event, state) -> None:
        """events received for any state"""
        self._logger.debug(
            f"{self.get_trace_header()}Before '{event}' in '{state.id}' state."
        )
        self._logger.info(
            f"{self.get_trace_header()}time spend in state {state.id} = {self.get_time_in_state()}sec"
        )

    # #################
    # dock
    # #################
    def on_enter_dock(self, source) -> None:
        self._logger.debug(
            f"{self.get_trace_header()}entered {self.STATUS_DOCK} - source state was {source.id}"
        )
        if source.id == self.STATUS_MOWING_COMPLETE:
            self._logger.info("###########################################")
            self._logger.info("Mowing complete")
            self._logger.info(
                "overall time = %s", self.format_time(self.get_total_time())
            )
            self.pause_mowing(self.STATUS_DOCK)
            self._logger.info("###########################################")
        else:
            self._logger.error(self.get_trace_header() + "Undefined transition")

    def on_exit_dock(self, target) -> None:
        self._logger.debug(
            f"{self.get_trace_header()}exiting {self.STATUS_DOCK} - target state is {target.id}"
        )

    # #################
    # mow
    # #################
    def on_enter_mow(self, source) -> None:
        self._logger.debug(
            f"{self.get_trace_header()}entered {self.STATUS_MOW} - source state was {source.id}"
        )

        self.start_mowing()
        if (source.id == self.STATUS_DOCK) or (
            source.id == self.STATUS_MOWING_COMPLETE
        ):
            self._logger.info(f"{self.get_trace_header()}starting mow timer")
        elif (source.id == self.STATUS_PAUSE) or (
            source.id == self.STATUS_MOWING_COMPLETE
        ):
            self._logger.info(f"{self.get_trace_header()}stopping pause timer")
        elif source.id == self.STATUS_MOW:
            self._logger.info(f"{self.get_trace_header()}resumt mow again")
            self.resume_mowing(self.STATUS_MOW)
        else:
            self._logger.info(
                f"{self.get_trace_header()}no action defined for {source.id}"
            )

    def on_exit_mow(self, target) -> None:
        self._logger.debug(
            f"{self.get_trace_header()}exiting {self.STATUS_MOW} - target state is {target.id}"
        )
        self.pause_mowing(self.STATUS_MOW)

    # #################
    # pause
    # #################
    def on_enter_pause(self, source) -> None:
        self._logger.debug(
            f"{self.get_trace_header()}entered {self.STATUS_PAUSE} - source state was {source.id}"
        )
        if (source.id == self.STATUS_MOW) or (source.id == self.STATUS_MOWING_COMPLETE):
            self.pause_mowing(self.STATUS_PAUSE)
            self._logger.debug(f"{self.get_trace_header()}starting pause timer")
        else:
            self._logger.error(self.get_trace_header() + "Undefined transition")

    def on_exit_pause(self, target) -> None:
        self._logger.debug(
            f"{self.get_trace_header()}exiting {self.STATUS_PAUSE} - target state is {target.id}"
        )

    # #################
    # mowing complete
    # #################
    def on_enter_mowing_complete(self, source) -> None:
        self._logger.debug(
            f"{self.get_trace_header()}entered {self.STATUS_DOCK} - source state was {source.id}"
        )
        if source.id == self.STATUS_MOW:
            self.stop_mowing(self.STATUS_MOW)
            self._logger.debug(f"{self.get_trace_header()}starting pause timer")
        else:
            self._logger.error(self.get_trace_header() + "Undefined transition")

    def on_exit_mowing_complete(self, target) -> None:
        self._logger.debug(
            f"{self.get_trace_header()}exiting {self.STATUS_MOWING_COMPLETE} - target state is {target.id}"
        )

    # #################
    # transition complete
    # #################
    def after_transition(self, event, state) -> None:
        """last function in state change queue"""
        self._logger.info(
            f"{self.get_trace_header()}is in state {state.id} due to event {event}"
        )
        self._time_state_entered = datetime.now()

    def get_action_timer(self) -> tuple[int, int]:
        self._logger.debug(
            self.get_trace_header() + "get_action_timer for state %s",
            self.current_state.name.lower(),
        )
        self._logger.debug("%s###########################", self.get_trace_header())
        self._logger.debug(
            "%smow_start_time   = %s",
            self.get_trace_header(),
            self.get_mow_start_time(),
        )
        self._logger.debug(
            "%total mow_duration     = %s",
            self.get_trace_header(),
            self.get_total_mow_duration_sec(self.get_state_name()),
        )
        self._logger.debug(
            "%scurrent mow_duration     = %s",
            self.get_trace_header(),
            self.get_new_mowing_duration_sec(self.get_state_name()),
        )
        self._logger.debug("%s###########################", self.get_trace_header())
        self._logger.debug(
            "%sprevious pause_duration   = %s",
            self.get_trace_header(),
            self.get_pause_duration_sec(self.get_state_name()),
        )
        self._logger.debug(
            "%scurrent pause_duration   = %s",
            self.get_trace_header(),
            self.get_new_pause_duration_sec(self.get_state_name()),
        )
        self._logger.debug("%s###########################", self.get_trace_header())
        if self.current_state.name.lower() == self.STATUS_DOCK:
            return self.get_total_mow_duration_sec(
                self.get_state_name()
            ), self.get_pause_duration_sec(self.get_state_name())

        if self.current_state.name.lower() == self.STATUS_MOW:
            pausetime = self.get_pause_duration_sec(self.get_state_name())
        else:
            pausetime = self.get_pause_duration_sec(
                self.get_state_name()
            ) + self.get_new_pause_duration_sec(self.get_state_name())
        mowtime = self.get_new_mowing_duration_sec(self.get_state_name()) - pausetime

        return mowtime, pausetime
