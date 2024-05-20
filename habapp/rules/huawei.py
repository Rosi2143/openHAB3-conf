"""handle changes in huawei items"""

# text to speech from https://ttsmp3.com/ai
# warnsounds from https://mixkit.co/free-sound-effects/alarm/

import logging
from datetime import timedelta

import HABApp
from HABApp.openhab.items import SwitchItem, StringItem, DimmerItem
from HABApp.openhab.events import (
    ItemStateChangedEvent,
    ItemStateChangedEventFilter,
)

logger = logging.getLogger("Huawei")
TEXT_TO_BLINK_RATIO = 20
MAX_WARN_LOOPS = 10 * TEXT_TO_BLINK_RATIO
MAX_END_INFO = 2 * TEXT_TO_BLINK_RATIO
TIME_BETWEEN_WARNINGS_SEC = 5


class Huawei(HABApp.Rule):
    """handle changes in huawei items"""

    def __init__(self):
        super().__init__()

        oh_item_off_grid = SwitchItem.get_item("HuaweiSolar_Battery_Switch_To_Off_Grid")
        oh_item_off_grid.listen_event(self.off_grid, ItemStateChangedEventFilter())

        self.warnjob = None
        self.endjob = None
        self.off_grid_counter = 0
        logger.info("Huawei started.")

    def off_grid(self, event):
        """
        handle off grid switch

        Args:
            event (_type_): triggering event
        """
        assert isinstance(event, ItemStateChangedEvent)
        logger.info(
            "rule fired because of %s %s --> %s",
            event.name,
            event.old_value,
            event.value,
        )

        if event.value == "ON":
            logger.error("Power Grid is down!")
            self.off_grid_counter = 0
            self.warnjob = self.run.every(
                start_time=0,
                interval=timedelta(seconds=TIME_BETWEEN_WARNINGS_SEC),
                callback=self.create_mp3_grid_off_warning,
            )
            self.endjob.cancel()
            self.endjob = None
        else:
            if event.old_value == "ON":
                logger.info("Power Grid is up again.")
                self.off_grid_counter = 0
                self.warnjob = self.run.every(
                    start_time=0,
                    interval=timedelta(seconds=TIME_BETWEEN_WARNINGS_SEC),
                    callback=self.create_mp3_grid_on_info,
                )
                self.warnjob.cancel()
                self.warnjob = None
            else:
                logger.info("Initial value received!")

    def create_mp3_grid_off_warning(self):
        """create mp3 warning"""
        if self.off_grid_counter > MAX_WARN_LOOPS:
            self.off_grid_counter = 0

            ColorItem_Color.send_command(save_color)
            ColorItem_Brightness.send_command(save_brightness)

            ColorItem_Soundfile.send_command(ColorItem_Soundfile)
            ColorItem_Soundfile.send_command(ColorItem_Soundlevel)
            self.warnjob.cancel()
            return

        ColorItem_Color = StringItem.get_item("Mp3Spieler_Color")
        ColorItem_Brightness = DimmerItem.get_item("Mp3Spieler_Level")
        ColorItem_Soundfile = StringItem.get_item("Mp3Spieler_1_SOUNDFILE")
        ColorItem_Soundlevel = StringItem.get_item("Mp3Spieler_1_LEVEL")
        if self.off_grid_counter == 0:
            save_color = ColorItem_Color.get_value()
            save_brightness = ColorItem_Brightness.get_value()
            save_soundfile = ColorItem_Soundfile.get_value()

        if self.off_grid_counter % 2 == 0:
            ColorItem_Color.send_command("RED")
            ColorItem_Brightness.send_command("100")
        else:
            ColorItem_Color.send_command(save_color)
            ColorItem_Brightness.send_command(save_brightness)

        if self.off_grid_counter % TEXT_TO_BLINK_RATIO == 0:
            ColorItem_Soundfile.send_command("SOUNDFILE_014")
            ColorItem_Soundfile.send_command("100")
        if self.off_grid_counter % TEXT_TO_BLINK_RATIO == 2:
            ColorItem_Soundfile.send_command(ColorItem_Soundfile)
            ColorItem_Soundfile.send_command(ColorItem_Soundlevel)
        self.off_grid_counter += 1

    def create_mp3_grid_on_info(self):
        """create mp3 info that grid is back"""
        if self.off_grid_counter > MAX_WARN_LOOPS:
            self.off_grid_counter = 0

            ColorItem_Color.send_command(save_color)
            ColorItem_Brightness.send_command(save_brightness)

            ColorItem_Soundfile.send_command(save_soundfile)
            ColorItem_Soundfile.send_command(save_soundfile)
            self.endjob.cancel()
            return

        ColorItem_Color = StringItem.get_item("Mp3Spieler_Color")
        ColorItem_Brightness = DimmerItem.get_item("Mp3Spieler_Level")
        ColorItem_Soundfile = StringItem.get_item("Mp3Spieler_1_SOUNDFILE")
        ColorItem_Soundlevel = StringItem.get_item("Mp3Spieler_1_LEVEL")
        if self.off_grid_counter == 0:
            save_color = ColorItem_Color.get_value()
            save_brightness = ColorItem_Brightness.get_value()
            save_soundfile = ColorItem_Soundfile.get_value()

        if self.off_grid_counter % 2 == 0:
            ColorItem_Color.send_command("Green")
            ColorItem_Brightness.send_command("100")
        else:
            ColorItem_Color.send_command(save_color)
            ColorItem_Brightness.send_command(save_brightness)

        if self.off_grid_counter % TEXT_TO_BLINK_RATIO == 0:
            ColorItem_Soundfile.send_command("SOUNDFILE_015")
            ColorItem_Soundfile.send_command("100")
        if self.off_grid_counter % TEXT_TO_BLINK_RATIO == 2:
            ColorItem_Soundfile.send_command(save_soundfile)
            ColorItem_Soundfile.send_command(save_soundfile)
        self.off_grid_counter += 1


Huawei()
