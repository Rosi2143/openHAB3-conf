"""Example of python module statemachine: https://pypi.org/project/python-statemachine/"""

# log:set INFO jsr223.jython.mp3_player_mode
# minimum version python-statemachine = 1.0.3

import sys
import os

from core.log import logging, LOG_PREFIX
from core.rules import rule
from core.triggers import when

OH_CONF = os.getenv('OPENHAB_CONF')

sys.path.append(os.path.join(OH_CONF, "automation/lib/python/personal"))
from security_door_window_statemachine import security_door_window_statemachine, get_state_machine_graph

log = logging.getLogger("{}.mp3_player_mode".format(LOG_PREFIX))

MP3_PLAYER_STATE_MACHINE = security_door_window_statemachine(
    "Kueche", log)

def set_mode_item(state, level):
    """set the mp3_player_mode item """
    events.sendCommand("Mp3Spieler_Color", state)
    events.sendCommand("Mp3Spieler_Level", str(level))

@rule("MP3_player_statemachine_create",
      description="initialize the statemachines for mp3-player device",
      tags=["systemstart", "mp3-player", "statemachines"])
@when("System started")
def initialize_mp3_player_statemachine(event):
    """setup all statemachines for mp3-player device"""

    # BellRang
    bell_rang_state = itemRegistry.getItem(
        "KlingelerkennungFlur_StoreState").state
    initialize_mp3_player_statemachine.log.info(
        "handling BellRang: (" + str(bell_rang_state) + ")")
    MP3_PLAYER_STATE_MACHINE.set_bell_rang(bell_rang_state == "ON")
    MP3_PLAYER_STATE_MACHINE.send("tr_bell_rang")

    # lock_error
    lock_error_state = itemRegistry.getItem("SchlossWaschkueche_Fehler").state
    initialize_mp3_player_statemachine.log.info(
        "handling window open: (" + str(lock_error_state) + ")")
    MP3_PLAYER_STATE_MACHINE.set_lock_error((lock_error_state == "ON"))
    MP3_PLAYER_STATE_MACHINE.send("tr_lock_error")

    # Outer_Door_Open
    outer_door_state = itemRegistry.getItem("gOuterDoors").state
    initialize_mp3_player_statemachine.log.info(
        "handling DoorOpen: (" + str(outer_door_state) + ")")
    MP3_PLAYER_STATE_MACHINE.set_outer_door_open((outer_door_state == "OPEN"))
    MP3_PLAYER_STATE_MACHINE.send("tr_outer_door_open")

    # Window_Open
    window_open = itemRegistry.getItem("gWindows").state
    initialize_mp3_player_statemachine.log.info(
        "handling open Windows: (" + str(window_open) + ")")
    MP3_PLAYER_STATE_MACHINE.set_window_open((window_open == "ON"))
    MP3_PLAYER_STATE_MACHINE.send("tr_window_open")

    set_mode_item(MP3_PLAYER_STATE_MACHINE.get_state_name(), \
                  MP3_PLAYER_STATE_MACHINE.get_light_level())

    get_state_machine_graph(MP3_PLAYER_STATE_MACHINE)

    initialize_mp3_player_statemachine.log.info("Done")

# ####################
# Rules
# ####################

# Check BellRang
@ rule("MP3_Player_BellRang_check",
       description="react on door bell",
       tags=["itemchange", "mp3_player", "statemachines", "bell"])
@when("Item KlingelerkennungFlur_StoreState changed")
def mp3_player_door_bell_rang(event):
    """
    send event to mp3 player statemachine if BellRang changes
    Args:
        event (_type_): any BellRang item
    """
    mp3_player_door_bell_rang.log.info(
        "rule fired because of %s %s --> %s", event.itemName, event.oldItemState, event.itemState)

    MP3_PLAYER_STATE_MACHINE.set_bell_rang((str(event.itemState)) == "ON")
    MP3_PLAYER_STATE_MACHINE.send("tr_bell_rang")
    set_mode_item(MP3_PLAYER_STATE_MACHINE.get_state_name(), MP3_PLAYER_STATE_MACHINE.get_light_level())

# Check lock_error
@rule("MP3_Player_Lock_Error",
      description="react on changes in Lock_Error",
      tags=["itemchange", "mp3_player", "statemachines", "lock_error"])
@when("Item SchlossWaschkueche_Fehler changed")
def mp3_player_door_lock_error(event):
    """
    send event to mp3 player statemachine if Lock_Error changes
    Args:
        event (_type_): any Lock_Error item
    """
    mp3_player_door_lock_error.log.info(
        "rule fired because of %s %s --> %s", event.itemName, event.oldItemState, event.itemState)

    MP3_PLAYER_STATE_MACHINE.set_lock_error(str(event.itemState) == "ON")
    MP3_PLAYER_STATE_MACHINE.send("tr_lock_error")
    set_mode_item(MP3_PLAYER_STATE_MACHINE.get_state_name(), MP3_PLAYER_STATE_MACHINE.get_light_level())

# Check Outer Doors
@rule("MP3_Player_outer_door_open",
      description="react on changes in Light",
      tags=["itemchange", "mp3_player", "statemachines", "outer_door_open"])
@when("Item gOuterDoors changed")
def mp3_player_outer_door_open(event):
    """
    send event to mp3 player statemachine if outer_door_open changes
    Args:
        event (_type_): any Light item
    """
    mp3_player_outer_door_open.log.info(
        "rule fired because of %s %s --> %s", event.itemName, event.oldItemState, event.itemState)

    MP3_PLAYER_STATE_MACHINE.set_outer_door_open(str(event.itemState) == "ON")
    MP3_PLAYER_STATE_MACHINE.send("tr_outer_door_open")
    set_mode_item(MP3_PLAYER_STATE_MACHINE.get_state_name(), MP3_PLAYER_STATE_MACHINE.get_light_level())

# Check window_open
@rule("mp3_Player_window_open",
      description="react on changes in window_open",
      tags=["itemchange", "mp3_player", "statemachines", "window_open"])
@when("Item gWindows changed")
def mp3_player_window_open(event):
    """
    send event to mp3 player statemachine if window_open changes
    Args:
        event (_type_): any window_open item
    """
    mp3_player_window_open.log.info(
        "rule fired because of %s %s --> %s", event.itemName, event.oldItemState, event.itemState)

    MP3_PLAYER_STATE_MACHINE.set_window_open(str(event.itemState) == "ON")
    MP3_PLAYER_STATE_MACHINE.send("tr_window_open")
    set_mode_item(MP3_PLAYER_STATE_MACHINE.get_state_name(), MP3_PLAYER_STATE_MACHINE.get_light_level())

# Check Timeout
@rule("MP3_Player_Timeout",
      description="react on changes in Timeout",
      tags=["itemchange", "mp3_player", "statemachines", "timeout"])
@when("Item Mp3Spieler_Timeout changed to OFF")
def mp3_player_timeout(event):
    """
    send event to mp3 player statemachine if Timeout changes
    Args:
        event (_type_): any Timeout item
    """
    mp3_player_timeout.log.info(
        "rule fired because of %s %s --> %s", event.itemName, event.oldItemState, event.itemState)

    MP3_PLAYER_STATE_MACHINE.set_timeout(True)
    MP3_PLAYER_STATE_MACHINE.send("tr_timeout")
    set_mode_item(MP3_PLAYER_STATE_MACHINE.get_state_name(), MP3_PLAYER_STATE_MACHINE.get_light_level())
