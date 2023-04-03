"""
This script handles event triggers for HABPanel items.
"""
# log:set INFO jsr223.jython.HABPanel

from core.log import logging, LOG_PREFIX
from core.rules import rule
from core.triggers import when

log = logging.getLogger("{}.habpanel".format(LOG_PREFIX))


@rule("HABPanel: Charge state",
      description="start or stop charging of the HABPanel",
      tags=["itemchange", "habpanel"])
@when("Item HABPanel_Battery_Level changed")
@when("Time cron 15 2/5 * 1/1 * ? *")
def check_charging_state(event):
    """
    check if HABPanel needs charging

    Args:
        event (_type_): triggering event
    """

    if event:
        check_charging_state.log.info(
            "rule fired because of %s", event.event)

    check_charging_state.log.debug(
        "HABPanel_Battery_Level = %s", items["HABPanel_Battery_Level"])

    check_charging_state.log.debug(
        "HABPanelLadung_Betrieb = %s", items["HABPanelLadung_Betrieb"])

    batteryLevel = 0
    chargingState = False

    if items["HABPanel_Battery_Level"] != "NULL":
        batteryLevel = items["HABPanel_Battery_Level"]
    if items["HABPanelLadung_Betrieb"] != "NULL":
        chargingState = items["HABPanelLadung_Betrieb"]

    if ((batteryLevel < 20) and not chargingState):
        events.sendCommand("HABPanelLadung_Betrieb", "ON")
        check_charging_state.log.info("start charging")
    elif ((batteryLevel > 90) and chargingState):
        events.sendCommand("HABPanelLadung_Betrieb", "OFF")
        check_charging_state.log.info("stop charging")
    else:
        check_charging_state.log.info(
            "No change: ChangeState=" + chargingState + " ChargeLevel=" + batteryLevel)


@rule("HABPanel: Proximity alert",
      description="turn the HABPanel on if someone get close",
      tags=["itemchange", "habpanel"])
# @when("Item HABPanel_Proximity changed to CLOSED")
@when("Item HABPanel_Motion changed to CLOSED")
def proximity_alert(event):
    """
    turn HABPanel on if someone gets close

    Args:
        event (_type_): triggering event
    """

    if event:
        proximity_alert.log.info(
            "rule fired because of %s", events.event)

    events.sendCommand("HABPanel_Command", "SCREEN_ON")
