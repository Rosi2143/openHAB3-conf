"""
This script handles motion detector mapping.
"""
# log:set INFO jsr223.jython.MotionDetect

from core.log import logging, LOG_PREFIX
from core.rules import rule
from core.triggers import when


# Homematic-IP
@rule("MotionDetect: FrontDoor",
      description="MotionDetector of FrontDoor",
      tags=["itemchange", "MotionDetect", "frontdoor"])
@when("Item BewegungsmelderHaustuer_Motion changed")
def motiondetect_frontdoor(event):
    """
    switch lamp with motion detect

    Args:
        event (_type_): triggering event
    """
    motiondetect_frontdoor.log.info(
        "rule fired because of %s %s --> %s", event.itemName, event.oldItemState, event.itemState)

    events.postUpdate(LichtHaustuer_State, event.itemState)


@rule("MotionDetect: BasementCorridor",
      description="MotionDetector of Basement Corridor",
      tags=["itemchange", "MotionDetect", "basementcorridor"])
@when("Item BewegungsmelderFlur_Motion changed")
def motiondetect_basement_corridor(event):
    """
    switch lamp with motion detect

    Args:
        event (_type_): triggering event
    """
    motiondetect_basement_corridor.log.info(
        "rule fired because of %s %s --> %s", event.itemName, event.oldItemState, event.itemState)

    events.postUpdate(LichtFlurKeller_State, event.itemState)


# IKEA
@rule("MotionDetect: GastWC",
      description="MotionDetector of GastWC",
      tags=["itemchange", "MotionDetect", "GuestWC", "mqtt"])
@when("Item BewegungsmelderGastWC_Motion changed")
def motiondetect_guest(event):
    """
    switch lamp with motion detect

    Args:
        event (_type_): triggering event
    """
    motiondetect_guest.log.info(
        "rule fired because of %s %s --> %s", event.itemName, event.oldItemState, event.itemState)

    events.postUpdate(LichtGastWC_State, event.itemState)


@rule("MotionDetect: Abstellraum",
      description="MotionDetector of Abstellraum",
      tags=["itemchange", "MotionDetect", "Abstellraum", "mqtt"])
@when("Item BewegungsmelderAbstellraum_Motion changed")
def motiondetect_guest(event):
    """
    switch lamp with motion detect

    Args:
        event (_type_): triggering event
    """
    motiondetect_guest.log.info(
        "rule fired because of %s %s --> %s", event.itemName, event.oldItemState, event.itemState)

    events.postUpdate(LichtAbstellraum_State, event.itemState)


@rule("MotionDetect: Gast",
      description="MotionDetector of Gast",
      tags=["itemchange", "MotionDetect", "Guest", "mqtt"])
@when("Item BewegungsmelderGaestezimmer_Motion changed")
def motiondetect_guest(event):
    """
    switch lamp with motion detect

    Args:
        event (_type_): triggering event
    """
    motiondetect_guest.log.info(
        "rule fired because of %s %s --> %s", event.itemName, event.oldItemState, event.itemState)

    events.postUpdate(LichtGast_State, event.itemState)


@rule("MotionDetect: Office",
      description="MotionDetector of Office",
      tags=["itemchange", "MotionDetect", "office", "mqtt"])
@when("Item BewegungsmelderBuero_Motion changed")
def motiondetect_office(event):
    """
    switch lamp with motion detect

    Args:
        event (_type_): triggering event
    """
    motiondetect_office.log.info(
        "rule fired because of %s %s --> %s", event.itemName, event.oldItemState, event.itemState)

    events.postUpdate(LichtBuero_State, event.itemState)


@rule("MotionDetect: Werkstatt",
      description="MotionDetector of Werkstatt",
      tags=["itemchange", "MotionDetect", "Werkstatt", "mqtt"])
@when("Item BewegungsmelderWerkstatt_Motion changed")
def motiondetect_werkstatt(event):
    """
    switch lamp with motion detect

    Args:
        event (_type_): triggering event
    """
    motiondetect_werkstatt.log.info(
        "rule fired because of %s %s --> %s", event.itemName, event.oldItemState, event.itemState)

    events.postUpdate(LichtWerkstatt_State, event.itemState)
