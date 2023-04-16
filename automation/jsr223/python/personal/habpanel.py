"""
This script handles event triggers for HABPanel items.
"""
# log:set INFO jsr223.jython.HABPanel

from core.log import logging, LOG_PREFIX
from core.rules import rule
from core.triggers import when

log = logging.getLogger("{}.habpanel".format(LOG_PREFIX))

BATTERY_MAX_CHARGE = 80
BATTERY_MIN_CHARGE = 40


@rule("HABPanel: Charge state",
      description="start or stop charging of the HABPanel",
      tags=["itemchange", "habpanel"])
@when("Item HABPanel_Battery_Level changed")
@when("Time cron 15 2/5 * 1/1 * ? *")
def check_charging_state(event):
    """check if HABPanel needs charging"""

    if event:
        check_charging_state.log.info(
            "rule fired because of %s", event.itemName)

    battery_level = 0
    charging_state = False

    if items["HABPanel_Battery_Level"] != "NULL":
        battery_level = items["HABPanel_Battery_Level"]
    if items["HABPanelLadung_Betrieb"] != "NULL":
        charging_state = items["HABPanelLadung_Betrieb"] == "ON"

    check_charging_state.log.debug(
        "HABPanel_Battery_Level = %s", battery_level)

    check_charging_state.log.debug(
        "HABPanelLadung_Betrieb = %s", charging_state)

    if ((battery_level < BATTERY_MIN_CHARGE) and not charging_state):
        events.sendCommand("HABPanelLadung_Betrieb", "ON")
        check_charging_state.log.info("start charging")
    elif ((battery_level > BATTERY_MAX_CHARGE) and charging_state):
        events.sendCommand("HABPanelLadung_Betrieb", "OFF")
        check_charging_state.log.info("stop charging")
    else:
        check_charging_state.log.info(
            "No change: ChargeState=" + str(charging_state) + " ChargeLevel=" + str(battery_level))


@rule("HABPanel: Proximity alert",
      description="turn the HABPanel on if someone get close",
      tags=["itemchange", "habpanel"])
# @when("Item HABPanel_Proximity changed to CLOSED")
@when("Item HABPanel_Motion changed")
def proximity_alert(event):
    """turn HABPanel on if someone gets close"""

    if event:
        proximity_alert.log.info(
            "rule fired because of %s --> %s", event.itemName, event.itemState)

    if str(event.itemState) == "OPEN":
        events.sendCommand("HABPanel_Command", "SCREEN_OFF")
    else:
        events.sendCommand("HABPanel_Command", "SCREEN_ON")
