"""Example of python module statemachine: https://pypi.org/project/python-statemachine/"""

# log:set INFO jsr223.jython.mp3_player_mode
# minimum version python-statemachine = 1.0.3
import logging  # required for extended logging

import sys
from datetime import timedelta

import HABApp
from HABApp.core.events import ValueChangeEvent, ValueChangeEventFilter
from HABApp.openhab.items import GroupItem, SwitchItem

log = logging.getLogger('MP3PlayerMode')

OH_CONF = "/etc/openhab/"

sys.path.append(OH_CONF + 'habapp/rules/')
from statemachines.SecurityDoorWindowStatemachine import SecurityDoorWindowStatemachine, get_state_machine_graph

MP3_PLAYER_STATE_MACHINE = SecurityDoorWindowStatemachine("Kueche", log)


class Mp3PlayerStatemachineRule(HABApp.Rule):
    """setup all statemachines for mp3-player device"""

    def __init__(self):
        """setup all statemachines for thermostats"""
        super().__init__()

        # BellRang
        bell_rang_item = SwitchItem.get_item("KlingelerkennungFlur_StoreState")
        bell_rang_state = bell_rang_item.get_value()
        log.info("##############################\nhandling BellRang: (%s)", str(
            bell_rang_state))
        MP3_PLAYER_STATE_MACHINE.set_bell_rang(bell_rang_state == "ON")
        MP3_PLAYER_STATE_MACHINE.send("tr_bell_rang")
        bell_rang_item.listen_event(
            self.door_bell_rang, ValueChangeEventFilter())

        # lock_error
        lock_error_item = SwitchItem.get_item("SchlossWaschkueche_Fehler")
        lock_error_state = lock_error_item.get_value()
        log.info("##############################\nhandling lock error: (%s)", str(
            lock_error_state))
        MP3_PLAYER_STATE_MACHINE.set_lock_error((lock_error_state == "ON"))
        MP3_PLAYER_STATE_MACHINE.send("tr_lock_error")
        lock_error_item.listen_event(
            self.door_lock_error, ValueChangeEventFilter())

        # Outer_Door_Open
        outer_door_item = GroupItem.get_item("gAussenTueren")
        outer_door_state = outer_door_item.get_value()
        log.info("##############################\nhandling DoorOpen: (%s)", str(
            outer_door_state))
        MP3_PLAYER_STATE_MACHINE.set_outer_door_open(
            (outer_door_state == "OPEN"))
        MP3_PLAYER_STATE_MACHINE.send("tr_outer_door_open")
        outer_door_item.listen_event(
            self.outer_door_open, ValueChangeEventFilter())

        # Window_Open
        window_open_item = GroupItem.get_item("gFenster")
        window_open_state = window_open_item.get_value()
        log.info("##############################\nhandling open Windows: (%s)", str(
            window_open_state))
        MP3_PLAYER_STATE_MACHINE.set_window_open((window_open_state == "ON"))
        MP3_PLAYER_STATE_MACHINE.send("tr_window_open")
        window_open_item.listen_event(
            self.window_open, ValueChangeEventFilter())

        self.set_mode_item(MP3_PLAYER_STATE_MACHINE.get_state_name(),
                           MP3_PLAYER_STATE_MACHINE.get_light_level())

        get_state_machine_graph(MP3_PLAYER_STATE_MACHINE)

        log.info("Done")

    def set_mode_item(self, state, level):
        """set the mp3_player_mode item"""
        self.openhab.send_command("Mp3Spieler_Color", state)
        self.openhab.send_command("Mp3Spieler_Level", str(level))

        timeout_sec = MP3_PLAYER_STATE_MACHINE.get_timeout_sec()
        if timeout_sec != 0:
            log.info("Start timer of %s sec", timeout_sec)
            self.run.at(time=timedelta(seconds=timeout_sec),
                        callback=self.timeout)

    # ####################
    # Rules
    # ####################

    # Check BellRang
    def door_bell_rang(self, event: ValueChangeEvent):
        """
        send event to mp3 player statemachine if BellRang changes
        Args:
            event (_type_): any BellRang item
        """
        log.info("##############################\nrule fired because of %s %s --> %s",
                 event.name,
                 event.old_value, event.value)

        MP3_PLAYER_STATE_MACHINE.set_bell_rang((str(event.value)) == "ON")
        MP3_PLAYER_STATE_MACHINE.send("tr_bell_rang")
        self.set_mode_item(MP3_PLAYER_STATE_MACHINE.get_state_name(),
                           MP3_PLAYER_STATE_MACHINE.get_light_level())

    # Check lock_error
    def door_lock_error(self, event: ValueChangeEvent):
        """
        send event to mp3 player statemachine if Lock_Error changes
        Args:
            event (_type_): any Lock_Error item
        """
        log.info("##############################\nrule fired because of %s %s --> %s",
                 event.name,
                 event.old_value, event.value)

        MP3_PLAYER_STATE_MACHINE.set_lock_error(str(event.value) == "ON")
        MP3_PLAYER_STATE_MACHINE.send("tr_lock_error")
        self.set_mode_item(MP3_PLAYER_STATE_MACHINE.get_state_name(),
                           MP3_PLAYER_STATE_MACHINE.get_light_level())

    # Check Outer Doors
    def outer_door_open(self, event: ValueChangeEvent):
        """
        send event to mp3 player statemachine if outer_door_open changes
        Args:
            event (_type_): any Light item
        """
        log.info("##############################\nrule fired because of %s %s --> %s",
                 event.name,
                 event.old_value, event.value)

        MP3_PLAYER_STATE_MACHINE.set_outer_door_open(
            str(event.value) == "OPEN")
        MP3_PLAYER_STATE_MACHINE.send("tr_outer_door_open")
        self.set_mode_item(MP3_PLAYER_STATE_MACHINE.get_state_name(),
                           MP3_PLAYER_STATE_MACHINE.get_light_level())

    # Check window_open
    def window_open(self, event: ValueChangeEvent):
        """
        send event to mp3 player statemachine if window_open changes
        Args:
            event (_type_): any window_open item
        """
        log.info("##############################\nrule fired because of %s %s --> %s",
                 event.name,
                 event.old_value, event.value)

        MP3_PLAYER_STATE_MACHINE.set_window_open(str(event.value) == "ON")
        MP3_PLAYER_STATE_MACHINE.send("tr_window_open")
        self.set_mode_item(MP3_PLAYER_STATE_MACHINE.get_state_name(),
                           MP3_PLAYER_STATE_MACHINE.get_light_level())

    # Check Timeout
    def timeout(self):
        """
        send event to mp3 player statemachine if Timeout changes
        Args:
            event (_type_): any Timeout item
        """
        log.info("##############################\nrule fired because of timeout")

        MP3_PLAYER_STATE_MACHINE.set_timeout_state(True)
        MP3_PLAYER_STATE_MACHINE.send("tr_timeout_state")
        self.set_mode_item(MP3_PLAYER_STATE_MACHINE.get_state_name(),
                           MP3_PLAYER_STATE_MACHINE.get_light_level())


Mp3PlayerStatemachineRule()
