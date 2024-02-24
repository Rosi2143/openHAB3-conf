"""Example of python module statemachine: https://pypi.org/project/python-statemachine/"""

# log:set INFO jsr223.jython.ThingState_statemachines_create
# minimum version python-statemachine = 1.0.3

import logging  # required for extended logging

import HABApp
from HABApp.openhab.items import GroupItem, SwitchItem
from HABApp.core.events import ValueChangeEventFilter
from HABApp.openhab import transformations

logger = logging.getLogger("Switch2Light")

param_file = "switch2light"
LONG_MAP = HABApp.DictParameter(param_file, "Long", default_value="")
SHORT_MAP = HABApp.DictParameter(param_file, "Short", default_value="")
TOGGLE_MAP = transformations.map["toggle.map"]


class Switch2Light(HABApp.Rule):
    """This class handles Hue internal states."""

    def __init__(self):
        """initialize the logger test"""
        super().__init__()


@rule(
    "ThingState_statemachines_create",
    description="initialize the statemachines for thing states",
    tags=["systemstart", "things", "statemachines"],
)
@when("System started")
def initialize_thingstate_statemachines(event):
    """setup all statemachines for thermostats"""

    for oh_thing in things.getAll():

        initialize_thingstate_statemachines.log.debug(
            "handling thing: " + oh_thing.getLabel() + "/" + str(oh_thing.getUID())
        )

        thing_UID = str(oh_thing.getUID())
        if "hue:" in thing_UID:

            if ":group:" in thing_UID:
                continue
            if ":bridge:" in thing_UID:
                continue

            thing_label = oh_thing.getLabel()
            thing_status = oh_thing.getStatus()

            initialize_thingstate_statemachines.log.info(
                "handling thing: %s -- %s / %s", thing_UID, thing_label, thing_status
            )

    initialize_thingstate_statemachines.log.info("Done")


# ####################
# Rules
# ####################

# Check BoostModes
