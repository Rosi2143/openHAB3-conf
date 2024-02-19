"""This script handles Homematic elements."""

import logging  # required for extended logging
from datetime import datetime, timedelta

import HABApp
from HABApp.openhab.items import SwitchItem, NumberItem, GroupItem, ContactItem
from HABApp.openhab.events.channel_events import ChannelTriggeredEvent
from HABApp.core.events import ValueChangeEvent, ValueChangeEventFilter, EventFilter

logger = logging.getLogger("Homematic")


class Homematic_CCU(HABApp.Rule):
    """This class handles Homematic-Raspi internal states."""

    def __init__(self):
        """initialize the logger test"""
        super().__init__()

        self.run.every(
            timedelta(seconds=6), timedelta(minutes=5), self.refresh_homematic_extras
        )
        logger.info("Homematic started")

        oh_item_commwd_timeout = SwitchItem.get_item("Homematic_CommWd_Timeout")
        oh_item_commwd_timeout.listen_event(
            self.homematic_comm_wd_timeout, ValueChangeEventFilter()
        )

        oh_item_comm_counter = NumberItem.get_item(
            "RaspiMaticGatewayExtras_Commcounter_Openhab"
        )
        oh_item_comm_counter.listen_event(
            self.homematic_comm_wd, ValueChangeEventFilter()
        )

        logger.info("Homematic started.")

    def refresh_homematic_extras(self):
        """send refresh to HomematicRaspi"""
        logger.debug("%s", self.refresh_homematic_extras.__name__)

        self.openhab.send_command("RaspiMaticGatewayExtras", "REFRESH")

    def homematic_comm_wd_timeout(self, event: ValueChangeEvent):
        """
        check communication

        Args:
            event (_type_): triggering event
        """
        logger.debug("%s", self.homematic_comm_wd_timeout.__name__)
        self.openhab.send_command("RaspiMaticGatewayExtras_Commcounter_Openhab", "0")
        logger.debug("Timer has executed")
        self.openhab.send_command(
            "RaspiMaticGatewayExtras_Commcounter_Error",
            NumberItem.get_item("RaspiMaticGatewayExtras_Commcounter_Error").get_value(
                default_value=0
            )
            + 1,
        )

        self.openhab.send_command("openHab_Binding_Restart_String", "none")
        self.run.at(timedelta(seconds=2), self.homematic_comm_wd_timeout_restart_bundle)

    def homematic_comm_wd_timeout_restart_bundle(self):
        logger.debug("%s", self.homematic_comm_wd_timeout_restart_bundle.__name__)
        self.openhab.send_command(
            "openHab_Binding_Restart_String", "org.openhab.binding.homematic"
        )

    def homematic_comm_wd(self, event: ValueChangeEvent):
        """
        check communication

        Args:
            event (_type_): triggering event
        """

        logger.debug(
            "%s : %d",
            self.homematic_comm_wd.__name__,
            NumberItem.get_item(
                "RaspiMaticGatewayExtras_Commcounter_Openhab"
            ).get_value(),
        )
        assert isinstance(event, ValueChangeEvent)
        logger.info("rule fired")

        self.openhab.send_command("Homematic_CommWd_Timeout", "OFF")


class Homematic_IP(HABApp.Rule):
    """create rules for homematic_ip elements"""

    def __init__(self):
        """initialize the logger test"""
        super().__init__()

        oh_item_shed_door = ContactItem.get_item("TuerSchuppen_OpenState")
        oh_item_shed_door.listen_event(self.shed_door, ValueChangeEventFilter())

        self.listen_event(
            'homematic:HmIP-DSD-PCB:homematicBridge-90f3312b69:0026DBE998F796:1#BUTTON',
            self.ring_start,
            EventFilter(ChannelTriggeredEvent, event="SHORT_PRESSED"),
        )

        oh_item_ring_long = SwitchItem.get_item("KlingelerkennungFlur_StoreState")
        oh_item_ring_long.listen_event(
            self.ring_end, ValueChangeEventFilter(value="OFF")
        )

        logger.info("Homematic_IP started.")

    def shed_door(self, event):
        """
        set light of shed

        Args:
            event (_type_): triggering event
        """
        logger.debug(
            "%s : %s",
            self.shed_door.__name__,
            SwitchItem.get_item("TuerSchuppen_OpenState").get_value(),
        )

        if str(event.value) == "OPEN":
            self.openhab.send_command("Schuppen_State", "ON")
        else:
            self.openhab.send_command("Schuppen_State", "OFF")

    def ring_start(self, event):
        """
        handle press on door bell

        Args:
            event (_type_): triggering event
        """

        logger.debug(
            "%s",
            self.ring_start.__name__,
        )

        self.openhab.send_command("HabPanelDashboardName", "CameraSnap")
        self.openhab.send_command("HABPanel_Command", "SCREEN_ON")
        self.openhab.send_command("HabPanelDashboardNameExp", "ON")
        self.openhab.send_command("KlingelerkennungFlur_StoreState", "ON")

    def ring_end(self, event):
        """
        door bell status was reset

        Args:
            event (_type_): triggering event
        """

        logger.debug(
            "%s",
            self.ring_end.__name__,
        )

        self.openhab.send_command("HabPanelDashboardName", "Erdgeschoss")


MAX_ALLOWED_TEMP = 27
NEW_ALLOWED_TEMP = 20
OVERHEAT_STRING = "_HitzeSchutzTimer"


class Homematic_Overheat(HABApp.Rule):
    """create rules for overheat protection"""

    def __init__(self):
        """initialize the logger test"""
        super().__init__()

        oh_group_thermostate_setpoints = GroupItem.get_item(
            "gThermostate_SetPointModes"
        )
        for oh_item in oh_group_thermostate_setpoints.members:
            oh_item.listen_event(
                self.overheat_protection_start, ValueChangeEventFilter()
            )

        oh_group_timer_expired = GroupItem.get_item("gThermostate_HitzeSchutzTimer")
        for oh_item in oh_group_timer_expired.members:
            oh_item.listen_event(
                self.overheat_protection_end, ValueChangeEventFilter(value="OFF")
            )

    def overheat_protection_start(self, event):
        """
        make sure the temperature is not too high for too long

        Args:
            event (_type_): triggering event
        """

        logger.info(
            "rule fired because of %s %s --> %s",
            event.name,
            event.old_value,
            event.value,
        )

        set_temp = int(event.value)

        if set_temp >= MAX_ALLOWED_TEMP:
            timer_item_name = event.name + OVERHEAT_STRING
            if self.openhab.item_exists(timer_item_name):
                logger.info("TimerItem: " + timer_item_name + " does not exist.")
            else:
                self.openhab.send_command(SwitchItem.get_item(timer_item_name), "ON")

    def overheat_protection_end(self, event):
        """
        set temperature back to "normal" after the timeout

        Args:
            event (_type_): triggering event
        """

        logger.info(
            "rule fired because of %s %s --> %s",
            event.name,
            event.old_value,
            event.value,
        )

        item_name = event.name.replace(OVERHEAT_STRING, "")
        set_temp = int(NumberItem.get_item(item_name).get_value())
        new_temp = str(NEW_ALLOWED_TEMP)

        if set_temp >= MAX_ALLOWED_TEMP:
            logger.info("Reset: %s to lower temperature of %d°C.", item_name, new_temp)
            self.openhab.send_command(item_name, new_temp)


class WindowState(HABApp.Rule):
    """set windowstates of thermostats"""

    def __init__(self):
        """initialize the logger test"""
        super().__init__()

        oh_group_window_state = GroupItem.get_item("gThermostate_WindowOpenStates")
        for oh_item in oh_group_window_state.get_members():
            oh_item.listen_event(
                self.window_open_state_handling, ValueChangeEventFilter()
            )

        logger.info("WindowState started")

    def window_open_state_handling(self, event):
        """set thermostat item depending on window open state"""

        logger.info(
            "rule fired because of %s %s --> %s",
            event.name,
            event.old_value,
            event.value,
        )

        windowstate_item_name = event.name.replace("_WindowOpenState", "_WindowState")
        if self.openhab.item_exists(windowstate_item_name):
            logger.info(
                "WindowOpenStateItem: %s does not exist.", windowstate_item_name
            )
        else:
            self.openhab.send_command(windowstate_item_name, str(event.value))


Homematic_CCU()
Homematic_IP()
Homematic_Overheat()
