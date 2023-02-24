"""
This script handles Homematic-Raspi internal states.
"""
# log:set INFO jsr223.jython.HomematicCCU

from core.log import logging, LOG_PREFIX
from core.rules import rule
from core.triggers import when


@rule("HomematicCCU: Refresh Extras",
      description="trigger Refresh of the HomematicCCU Extras",
      tags=["cron", "HomematicCCU"])
@when("Time cron 15 2/5 * 1/1 * ? *")
def refresh_homematic_extras(event):
    """
    send refresh to HomematicRaspi

    Args:
        event (_type_): triggering event
    """

    events.sendCommand("RaspiMaticGatewayExtras", "REFRESH")


log = logging.getLogger("{}.homematic_ccu".format(LOG_PREFIX))


@rule("HomematicCCU: Comm Watchdog Timeout",
      description="handle watchdog timeout",
      tags=["itemchange", "HomematicCCU", "watchdog"])
# @when("Item HomematicCCU_Proximity changed to CLOSED")
@when("Item Homematic_CommWd_Timeout changed")
def homematic_comm_wd_timeout(event):
    """
    check communication

    Args:
        event (_type_): triggering event
    """
    events.sendCommand("RaspiMaticGatewayExtras_Commcounter_Openhab", "0")
    homematic_comm_wd_timeout.log.debug("Timer has executed")
    events.postUpdate("RaspiMaticGatewayExtras_Commcounter_Error",
                      str(items["RaspiMaticGatewayExtras_Commcounter_Error"] + 1))
    events.postUpdate("openHab_Binding_Restart_String", "none")
    sleep(50 / 1000)
    events.postUpdate("openHab_Binding_Restart_String",
                      "org.openhab.binding.homematic")


@rule("HomematicCCU: Check Comm Watchdog",
      description="check if communication with homematic raspi is OK",
      tags=["itemchange", "HomematicCCU", "watchdog"])
# @when("Item HomematicCCU_Proximity changed to CLOSED")
@when("Item RaspiMaticGatewayExtras_Commcounter_Openhab changed")
def homematic_comm_wd(event):
    """
    check communication

    Args:
        event (_type_): triggering event
    """

    homematic_comm_wd.log.info(
        "rule fired")

    events.postUpdate("Homematic_CommWd_Timeout", "OFF")
