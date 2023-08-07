"""Example of python module statemachine: https://pypi.org/project/python-statemachine/"""

# log:set INFO jsr223.jython.door_lock_mode
# minimum version python-statemachine = 1.0.3

import logging  # required for extended logging

import sys
import HABApp
from HABApp.core.events import ValueChangeEvent, ValueChangeEventFilter
from HABApp.openhab.items import ContactItem, GroupItem, StringItem, SwitchItem

log = logging.getLogger('DoorLockMode')

OH_CONF = "/etc/openhab/"  # os.getenv('OPENHAB_CONF')

sys.path.append(OH_CONF + 'habapp/rules/')
from statemachines.DoorLockStatemachine import DoorLockStatemachine, get_state_machine_graph

DOOR_LOCK_STATE_MACHINE = door_lock_state_machine = DoorLockStatemachine(
    "WaschKueche", log)


class DoorLockStatemachineRule(HABApp.Rule):
    """setup all statemachines for door lock device"""

    def __init__(self):
        """setup all statemachines for thermostats"""
        super().__init__()

        thing_name = "SchlossWaschkueche"

        # CONFIG_PENDING
        config_pending_item = SwitchItem.get_item(
            thing_name + "_ConfigPending")
        config_pending_state = config_pending_item.get_value()
        log.info("handling Config Pending: (%s)", str(config_pending_state))
        DOOR_LOCK_STATE_MACHINE.set_lock_error(
            DOOR_LOCK_STATE_MACHINE.CONFIG_PENDING, (config_pending_state == "ON"))
        DOOR_LOCK_STATE_MACHINE.send("tr_error_change")
        config_pending_item.listen_event(
            self.error_changes, ValueChangeEventFilter())

        # ERROR_JAMMED
        error_jammed_item = SwitchItem.get_item(
            thing_name + "_ErrorJammed")
        error_jammed_state = error_jammed_item.get_value()
        log.info("handling Error Jammed: (%s)", str(error_jammed_state))
        DOOR_LOCK_STATE_MACHINE.set_lock_error(
            DOOR_LOCK_STATE_MACHINE.JAMMED, (error_jammed_state == "ON"))
        DOOR_LOCK_STATE_MACHINE.send("tr_error_change")
        error_jammed_item.listen_event(
            self.error_changes, ValueChangeEventFilter())

        # UNREACHABLE
        unreachable_item = SwitchItem.get_item(
            thing_name + "_Unreachable")
        unreachable_state = unreachable_item.get_value()
        log.info("handling Unreachable: (%s)", str(unreachable_state))
        DOOR_LOCK_STATE_MACHINE.set_lock_error(
            DOOR_LOCK_STATE_MACHINE.UNREACHABLE, (unreachable_state == "ON"))
        DOOR_LOCK_STATE_MACHINE.send("tr_error_change")
        unreachable_item.listen_event(
            self.error_changes, ValueChangeEventFilter())

        # REPORTED_LOCK_STATE
        reported_lock_item = StringItem.get_item(
            thing_name + "_LockState")
        reported_lock_state = reported_lock_item.get_value()
        log.info("handling reported LockState: (%s)", str(reported_lock_state))
        DOOR_LOCK_STATE_MACHINE.set_reported_lock(str(reported_lock_state))
        DOOR_LOCK_STATE_MACHINE.send("tr_reported_lock_change")
        reported_lock_item.listen_event(
            self.reported_lock_changes, ValueChangeEventFilter())

        # DarkOutside
        dark_outside_item = StringItem.get_item(
            "Sonnendaten_Sonnenphase")
        dark_outside_state = dark_outside_item.get_value()
        log.info("handling DarkOutside: (%s)", str(dark_outside_state))
        DOOR_LOCK_STATE_MACHINE.set_dark_outside(
            self.is_dark_outside(str(dark_outside_state)))
        DOOR_LOCK_STATE_MACHINE.send("tr_dark_outside_change")
        dark_outside_item.listen_event(
            self.dark_outside_changes, ValueChangeEventFilter())

        # Presence
        presence_item = GroupItem.get_item("gAnwesenheit")
        presence_state = presence_item.get_value()
        log.info("handling Presence: (%s)", str(presence_state))
        DOOR_LOCK_STATE_MACHINE.set_door_open((presence_state == "ON"))
        DOOR_LOCK_STATE_MACHINE.send("tr_presence_change")
        presence_item.listen_event(
            self.presence_changed, ValueChangeEventFilter())

        # DoorState
        door_open_item = ContactItem.get_item(
            "TuerWaschkueche_OpenState")
        door_open_state = door_open_item.get_value()
        log.info("handling DoorOpen: (%s)", str(door_open_state))
        DOOR_LOCK_STATE_MACHINE.set_door_open((door_open_state == "OPEN"))
        DOOR_LOCK_STATE_MACHINE.send("tr_door_open_change")
        door_open_item.listen_event(
            self.door_open_state_changes, ValueChangeEventFilter())

        # TerraceLight
        terrace_light_item = SwitchItem.get_item(
            "LichtTerrasseUnten_State")
        terrace_light_state = terrace_light_item.get_value()
        log.info("handling Terrace Light: (%s)", str(terrace_light_state))
        DOOR_LOCK_STATE_MACHINE.set_light((terrace_light_state == "ON"))
        DOOR_LOCK_STATE_MACHINE.send("tr_error_change")
        terrace_light_item.listen_event(
            self.light_changed, ValueChangeEventFilter())

        self.set_mode_item(DOOR_LOCK_STATE_MACHINE.get_state_name())

        get_state_machine_graph(DOOR_LOCK_STATE_MACHINE)

        log.info("Done")

    def set_mode_item(self, state):
        """set the door_lock_mode item """
        self.openhab.send_command("SchlossWaschkueche_LockTargetLevel", state)
        self.openhab.send_command("SchlossWaschkueche_Mode", state)

    def is_dark_outside(self, sun_phase):
        """checks if it is dark outside"""
        if ((sun_phase == "NAUTIC_DUSK") | (sun_phase == "ASTRO_DUSK") |
                (sun_phase == "NIGHT") | (sun_phase == "ASTRO_DAWN") |
                (sun_phase == "NAUTIC_DAWN")
                ):
            return True
        else:
            return False

    # ####################
    # Rules
    # ####################

    # Check ReportedLock
    def reported_lock_changes(self, event: ValueChangeEvent):
        """
        send event to DoorLock statemachine if ReportedLock changes
        Args:
            event (_type_): any ReportedLock item
        """
        log.info("rule fired because of %s %s --> %s", event.name,
                 event.old_value, event.value)

        DOOR_LOCK_STATE_MACHINE.set_reported_lock(str(event.value))
        DOOR_LOCK_STATE_MACHINE.send("tr_reported_lock_change")
        self.set_mode_item(DOOR_LOCK_STATE_MACHINE.get_state_name())

    # Check DarkOutside
    def dark_outside_changes(self, event: ValueChangeEvent):
        """
        send event to DoorLock statemachine if DarkOutside changes
        Args:
            event (_type_): any DarkOutside item
        """
        log.info(
            "rule fired because of %s %s --> %s", event.name, event.old_value, event.value)

        DOOR_LOCK_STATE_MACHINE.set_dark_outside(
            self.is_dark_outside(str(event.value)))
        DOOR_LOCK_STATE_MACHINE.send("tr_dark_outside_change")
        self.set_mode_item(DOOR_LOCK_STATE_MACHINE.get_state_name())

    # Check Presence
    def presence_changed(self, event: ValueChangeEvent):
        """
        send event to DoorLock statemachine if Presence changes
        Args:
            event (_type_): any Presence item
        """
        log.info(
            "rule fired because of %s %s --> %s", event.name, event.old_value, event.value)

        DOOR_LOCK_STATE_MACHINE.set_presence(str(event.value) == "ON")
        DOOR_LOCK_STATE_MACHINE.send("tr_presence_change")
        self.set_mode_item(DOOR_LOCK_STATE_MACHINE.get_state_name())

    # Check DoorState
    def door_open_state_changes(self, event: ValueChangeEvent):
        """
        send event to DoorLock statemachine if DoorState changes
        Args:
            event (_type_): any DoorState item
        """
        log.info(
            "rule fired because of %s %s --> %s", event.name, event.old_value, event.value)

        DOOR_LOCK_STATE_MACHINE.set_door_open(str(event.value) == "ON")
        DOOR_LOCK_STATE_MACHINE.send("tr_door_open_change")
        self.set_mode_item(DOOR_LOCK_STATE_MACHINE.get_state_name())

    # Check Light
    def light_changed(self, event: ValueChangeEvent):
        """
        send event to DoorLock statemachine if Light changes
        Args:
            event (_type_): any Light item
        """
        log.info(
            "rule fired because of %s %s --> %s", event.name, event.old_value, event.value)

        DOOR_LOCK_STATE_MACHINE.set_light(str(event.value) == "ON")
        DOOR_LOCK_STATE_MACHINE.send("tr_light_change")
        self.set_mode_item(DOOR_LOCK_STATE_MACHINE.get_state_name())

    # Check Errors
    def error_changes(self, event: ValueChangeEvent):
        """
        send event to DoorLock statemachine if error items change
        Args:
            event (_type_): any ErrorState item
        """
        log.info(
            "rule fired because of %s %s --> %s", event.name, event.old_value, event.value)

        error_type = ""
        if event.name.includes("ConfigPending"):
            error_type = DOOR_LOCK_STATE_MACHINE.CONFIG_PENDING
        elif event.name.includes("ErrorJammed"):
            error_type = DOOR_LOCK_STATE_MACHINE.JAMMED
        elif event.name.includes("Unreachable"):
            error_type = DOOR_LOCK_STATE_MACHINE.UNREACHABLE
        else:
            log.error("Unknown event %s", event.name)

        DOOR_LOCK_STATE_MACHINE.set_lock_error(
            error_type, str(event.value) == "ON")
        DOOR_LOCK_STATE_MACHINE.send("tr_error_change")
        self.set_mode_item(DOOR_LOCK_STATE_MACHINE.get_state_name())


DoorLockStatemachineRule()
