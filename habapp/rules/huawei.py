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

        self.save_color = "Black"
        self.save_brightness = 0
        self.save_soundfile = "NO_SOUNDFILE"
        self.save_soundlevel = 0

        self.ColorItem_Color = StringItem.get_item("Mp3Spieler_Color")
        self.ColorItem_Brightness = DimmerItem.get_item("Mp3Spieler_Level")
        self.ColorItem_Soundfile = StringItem.get_item("Mp3Spieler_2_SOUNDFILE")
        self.ColorItem_Soundlevel = DimmerItem.get_item("Mp3Spieler_2_LEVEL")

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
            if self.endjob is not None:
                self.endjob.cancel()
                self.endjob = None
                self.ColorItem_Color.oh_post_update_if(
                    self.save_color, not_equal=self.save_color
                )
                self.ColorItem_Brightness.oh_post_update_if(
                    self.save_brightness, not_equal=self.save_brightness
                )
                self.ColorItem_Soundfile.oh_post_update_if(
                    self.save_soundfile, not_equal=self.save_soundfile
                )
                self.ColorItem_Soundlevel.oh_post_update_if(
                    self.save_soundlevel, not_equal=self.save_soundlevel
                )

            self.save_color = self.ColorItem_Color.get_value()
            self.save_brightness = self.ColorItem_Brightness.get_value()
            self.save_soundfile = self.ColorItem_Soundfile.get_value()
            self.save_soundlevel = self.ColorItem_Soundlevel.get_value()

            self.warnjob = self.run.every(
                start_time=timedelta(0),
                interval=timedelta(seconds=TIME_BETWEEN_WARNINGS_SEC),
                callback=self.create_mp3_grid_off_warning,
            )
        else:
            if event.old_value == "ON":
                logger.info("Power Grid is up again.")
                self.off_grid_counter = 0
                if self.warnjob is not None:
                    self.warnjob.cancel()
                    self.warnjob = None
                    self.ColorItem_Color.oh_post_update_if(
                        self.save_color, not_equal=self.save_color
                    )
                    self.ColorItem_Brightness.oh_post_update_if(
                        self.save_brightness, not_equal=self.save_brightness
                    )
                    self.ColorItem_Soundfile.oh_post_update_if(
                        self.save_soundfile, not_equal=self.save_soundfile
                    )
                    self.ColorItem_Soundlevel.oh_post_update_if(
                        self.save_soundlevel, not_equal=self.save_soundlevel
                    )

                self.save_color = self.ColorItem_Color.get_value()
                self.save_brightness = self.ColorItem_Brightness.get_value()
                self.save_soundfile = self.ColorItem_Soundfile.get_value()
                self.save_soundlevel = self.ColorItem_Soundlevel.get_value()

                self.endjob = self.run.every(
                    start_time=timedelta(0),
                    interval=timedelta(seconds=TIME_BETWEEN_WARNINGS_SEC),
                    callback=self.create_mp3_grid_on_info,
                )
            else:
                logger.info("Initial value received!")

    def create_mp3_grid_off_warning(self):
        """create mp3 warning"""

        if self.off_grid_counter > MAX_WARN_LOOPS:
            self.off_grid_counter = 0

            self.ColorItem_Color.oh_post_update_if(
                self.save_color, not_equal=self.save_color
            )
            self.ColorItem_Brightness.oh_post_update_if(
                self.save_brightness, not_equal=self.save_brightness
            )
            self.ColorItem_Soundfile.oh_post_update_if(
                self.save_soundfile, not_equal=self.save_soundfile
            )
            self.ColorItem_Soundlevel.oh_post_update_if(
                self.save_soundlevel, not_equal=self.save_soundlevel
            )

            if self.warnjob is not None:
                self.warnjob.cancel()
            return

        logger.info("create_mp3_grid_off_warning: %s", self.off_grid_counter)

        if self.off_grid_counter % 2 == 0:
            logger.info("RED / 100")
            self.ColorItem_Color.oh_post_update_if("RED", not_equal="RED")
            self.ColorItem_Brightness.oh_post_update_if("100", not_equal="100")
        else:
            logger.info("%s / %d", self.save_color, self.save_brightness)
            self.ColorItem_Color.oh_post_update_if(
                self.save_color, not_equal=self.save_color
            )
            self.ColorItem_Brightness.oh_post_update_if(
                self.save_brightness, not_equal=self.save_brightness
            )

        if self.off_grid_counter % TEXT_TO_BLINK_RATIO == 0:
            logger.info("SOUNDFILE_014 / 100")
            self.ColorItem_Soundfile.oh_post_update_if(
                "SOUNDFILE_014", not_equal="SOUNDFILE_014"
            )
            self.ColorItem_Soundlevel.oh_post_update_if("100", not_equal="100")
        if self.off_grid_counter % TEXT_TO_BLINK_RATIO == TEXT_TO_BLINK_RATIO / 2:
            logger.info("%s / %d", self.save_soundfile, self.save_soundlevel)
            self.ColorItem_Soundfile.oh_post_update_if(
                self.save_soundfile, not_equal=self.save_soundfile
            )
            self.ColorItem_Soundlevel.oh_post_update_if(
                self.save_soundlevel, not_equal=self.save_soundlevel
            )
        self.off_grid_counter += 1

    def create_mp3_grid_on_info(self):
        """create mp3 info that grid is back"""

        if self.off_grid_counter > MAX_WARN_LOOPS:
            self.off_grid_counter = 0

            self.ColorItem_Color.oh_post_update_if(
                self.save_color, not_equal=self.save_color
            )
            self.ColorItem_Brightness.oh_post_update_if(
                self.save_brightness, not_equal=self.save_brightness
            )

            self.ColorItem_Soundfile.oh_post_update_if(
                self.save_soundfile, not_equal=self.save_soundfile
            )
            self.ColorItem_Soundlevel.oh_post_update_if(
                self.save_soundlevel, not_equal=self.save_soundlevel
            )
            if self.endjob is not None:
                self.endjob.cancel()
            return

        logger.info("create_mp3_grid_on_info: %s", self.off_grid_counter)

        if self.off_grid_counter % 2 == 0:
            logger.info("Green / 100")
            self.ColorItem_Color.oh_post_update_if("Green", not_equal="Green")
            self.ColorItem_Brightness.oh_post_update_if("100", not_equal="100")
        else:
            logger.info("%s / %d", self.save_color, self.save_brightness)
            self.ColorItem_Color.oh_post_update_if(
                self.save_color, not_equal=self.save_color
            )
            self.ColorItem_Brightness.oh_post_update_if(
                self.save_brightness, not_equal=self.save_brightness
            )

        if self.off_grid_counter % TEXT_TO_BLINK_RATIO == 0:
            logger.info("SOUNDFILE_015 / 100")
            self.ColorItem_Soundfile.oh_post_update_if(
                "SOUNDFILE_015", not_equal="SOUNDFILE_015"
            )
            self.ColorItem_Soundlevel.oh_post_update_if("100", not_equal="100")
        if self.off_grid_counter % TEXT_TO_BLINK_RATIO == TEXT_TO_BLINK_RATIO / 2:
            logger.info("%s / %d", self.save_soundfile, self.save_soundlevel)
            self.ColorItem_Soundfile.oh_post_update_if(
                self.save_soundfile, not_equal=self.save_soundfile
            )
            self.ColorItem_Soundlevel.oh_post_update_if(
                self.save_soundlevel, not_equal=self.save_soundlevel
            )
        self.off_grid_counter += 1


Huawei()
