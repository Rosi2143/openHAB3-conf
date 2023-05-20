"""Example of python module statemachine: https://pypi.org/project/python-statemachine/"""

# log:set INFO jsr223.jython.ThingState_statemachines_create
# minimum version python-statemachine = 1.0.3

import sys
import os

from core.log import logging, LOG_PREFIX
from core.rules import rule
from core.triggers import when

OH_CONF = os.getenv('OPENHAB_CONF')

sys.path.append(os.path.join(OH_CONF, "automation/lib/python/personal"))
from hue_offline_statemachine import get_state_machine, HueOfflineStatemachine

log = logging.getLogger("{}.thing_state".format(LOG_PREFIX))

# openhab:things list | grep hue:0
thing_state_map = {
    "hue:0210:ecb5fa2c8738:5": "",
    "hue:0220:ecb5fa2c8738:6": "",
    "hue:0220:ecb5fa2c8738:7": "",
    "hue:0220:ecb5fa2c8738:8": "",
    "hue:0010:ecb5fa2c8738:9": "",
    "hue:0010:ecb5fa2c8738:10": "",
    "hue:0220:ecb5fa2c8738:11": "",
    "hue:0220:ecb5fa2c8738:12": "",
    "hue:0220:ecb5fa2c8738:13": "",
    "hue:0220:ecb5fa2c8738:14": "",
    "hue:0220:ecb5fa2c8738:15": "",
    "hue:0220:ecb5fa2c8738:16": "",
    "hue:0100:ecb5fa2c8738:17": "",
    "hue:0220:ecb5fa2c8738:18": "",
    "hue:0010:ecb5fa2c8738:19": "",
    "hue:0010:ecb5fa2c8738:20": "",
    "hue:0010:ecb5fa2c8738:21": "",
    "hue:0100:ecb5fa2c8738:23": "",
    "hue:0840:ecb5fa2c8738:50": "",
    "hue:0840:ecb5fa2c8738:69": "",
}

thing_refresh_map = {
    "hue:0107:ecb5fa2c8738:2": "BewegungsmelderEinfahrt",
    "hue:0106:ecb5fa2c8738:3": "eLichtSensorEinfahrt",
    "hue:0302:ecb5fa2c8738:4": "TempSensorEinfahrt",
    "hue:0107:ecb5fa2c8738:31": "BewegungsmelderErkerweg",
    "hue:0107:ecb5fa2c8738:32": "LichtSensorErkerWeg",
    "hue:0302:ecb5fa2c8738:33": "TempSensorErkerWeg"
}


@rule("ThingState_statemachines_create",
      description="initialize the statemachines for thing states",
      tags=["systemstart", "things", "statemachines"])
@when("System started")
def initialize_thingstate_statemachines(event):
    """setup all statemachines for thermostats"""

    for oh_thing in things.getAll():

        initialize_thingstate_statemachines.log.debug(
            "handling thing: " + oh_thing.getLabel() + "/" + str(oh_thing.getUID()))

        thing_UID = str(oh_thing.getUID())
        if "hue:" in thing_UID:

            if ":group:" in thing_UID:
                continue
            if ":bridge:" in thing_UID:
                continue

            thing_label = oh_thing.getLabel()
            thing_status = oh_thing.getStatus()

            initialize_thingstate_statemachines.log.info(
                "handling thing: %s -- %s / %s",
                thing_UID,
                thing_label,
                thing_status)

    initialize_thingstate_statemachines.log.info("Done")

# ####################
# Rules
# ####################

# Check BoostModes
