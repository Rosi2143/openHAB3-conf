"""provide base classes for fading items
   currently supported are

   - WhiteLight (brightness)
   - AmbientLight (brightness, color temperature)
   - ColorLight (3 color rgb)
"""

import logging

from HABApp import Rule
from HABApp.openhab.items import ColorItem, DimmerItem, NumberItem, SwitchItem
from HABApp.core.events import ValueChangeEvent, ValueChangeEventFilter
from HABApp.util import Fade

logger = logging.getLogger("Fader")


class FadeDimmer(Rule):
    def __init__(
        self,
        oh_fadetrigger_item_name,
        oh_fadeduration_item_name,
        oh_power_item_name,
        oh_dimmer_item_name,
    ):
        super().__init__()
        self.power_item = SwitchItem.get_item(oh_power_item_name)

        self.dimmer_item = DimmerItem.get_item(oh_dimmer_item_name)
        self.fade_dimmer = Fade(callback=self.fade_dimmer_action)

        self.on_off_item = SwitchItem.get_item(oh_fadetrigger_item_name)
        self.on_off_item.listen_event(
            callback=self.fade_start,
            event_filter=ValueChangeEventFilter(value="ON"),
        )
        self.on_off_item.listen_event(
            callback=self.fade_stop,
            event_filter=ValueChangeEventFilter(value="OFF"),
        )

        self.duration_item = NumberItem.get_item(oh_fadeduration_item_name)
        self.duration_item.listen_event(
            callback=self.set_duration, event_filter=ValueChangeEventFilter()
        )
        self.duration_time = int(self.duration_item.get_value(default_value=180))

        self.dimmer_direction = "UP"
        logger.info("%s: FadeDimmer initialized.", oh_power_item_name)

    def set_duration(self, event):
        self.duration_time = int(event.value)
        logger.info(
            "%s: Fader duration set to %d",
            self.power_item.name,
            int(event.value),
        )
        if self.power_item.is_on():
            self.fade_stop(ValueChangeEvent(name="stop", value=0, old_value=0))
            self.fade_start(ValueChangeEvent(name="start", value=0, old_value=0))

    def fade_start(self, event):
        assert isinstance(event, ValueChangeEvent)

        min_step_duration = 5
        if self.duration_time / 10 < 10:
            min_step_duration = 2

        if self.dimmer_direction == "UP":
            self.fade_dimmer.setup(
                start_value=0,
                stop_value=100,
                duration=self.duration_time,
                min_step_duration=min_step_duration,
            )
        else:
            self.fade_dimmer.setup(
                start_value=100,
                stop_value=0,
                duration=self.duration_time,
                min_step_duration=min_step_duration,
            )
        self.fade_dimmer.schedule_fade()
        self.fade_dimmer_action(ValueChangeEvent(name="start", value=0, old_value=0))
        self.power_item.on()
        logger.info(
            "%s: Fading started --> %s. Duration = %d",
            self.power_item.name,
            self.dimmer_direction,
            self.duration_time,
        )

    def fade_stop(self, event):
        assert isinstance(event, ValueChangeEvent)

        logger.info("%s: Fading stopped.", self.power_item.name)
        self.fade_dimmer.stop_fade()
        self.power_item.off()

    def fade_dimmer_action(self, value):
        dimmer_value = int(self.fade_dimmer.get_value())
        logger.info(
            "%s: Fade value brightness: %d",
            self.power_item.name,
            dimmer_value,
        )
        self.dimmer_item.percent(dimmer_value)

        if self.fade_dimmer.is_finished:
            if self.dimmer_direction == "UP":
                self.dimmer_direction = "DOWN"
            else:
                self.dimmer_direction = "UP"
            self.fade_start(ValueChangeEvent(name="stop", value=0, old_value=0))


class FadeAmbient(FadeDimmer):
    def __init__(
        self,
        oh_fadetrigger_item_name,
        oh_fadeduration_item_name,
        oh_power_item_name,
        oh_dimmer_item_name,
        oh_temp_color_item_name,
    ):
        super().__init__(
            oh_fadetrigger_item_name=oh_fadetrigger_item_name,
            oh_fadeduration_item_name=oh_fadeduration_item_name,
            oh_power_item_name=oh_power_item_name,
            oh_dimmer_item_name=oh_dimmer_item_name,
        )
        self.temp_color_item = DimmerItem.get_item(oh_temp_color_item_name)
        self.fade_temp_color = Fade(callback=self.fade_ambient_action)

        self.color_direction = "Warm"
        logger.info("%s: FadeAmbient initialized.", oh_power_item_name)

    def fade_start(self, event):
        assert isinstance(event, ValueChangeEvent)
        logger.info("%s: Fading started.", self.power_item.name)
        min_step_duration = 5
        if self.duration_time / 10 < 10:
            min_step_duration = 2

        if self.fade_temp_color == "Warm":
            self.fade_temp_color.setup(
                start_value=0,
                stop_value=100,
                duration=self.duration_time * 2.33333,
                min_step_duration=min_step_duration,
            )
        else:
            self.fade_temp_color.setup(
                start_value=100,
                stop_value=0,
                duration=self.duration_time * 2.33333,
                min_step_duration=min_step_duration,
            )
        self.fade_temp_color.schedule_fade()
        self.fade_ambient_action(0)
        super().fade_start(ValueChangeEvent(name="start", value=0, old_value=0))

    def fade_stop(self, event):
        assert isinstance(event, ValueChangeEvent)
        logger.info("%s: Fading stopped.", self.power_item.name)
        self.fade_temp_color.stop_fade()
        super().fade_stop(ValueChangeEvent(name="stop", value=0, old_value=0))

    def fade_ambient_action(self, value):
        dimmer_value = int(self.fade_dimmer.get_value())
        color_temp = int(self.fade_temp_color.get_value())
        logger.info(
            "%s: Fade value brightness: %d - color_temp: %d",
            self.power_item.name,
            dimmer_value,
            color_temp,
        )

        if self.fade_temp_color.is_finished:
            if self.dimmer_direction == "Warm":
                self.dimmer_direction = "Cool"
            else:
                self.dimmer_direction = "Warm"
            self.fade_start(ValueChangeEvent(name="stop", value=0, old_value=0))
        self.temp_color_item.percent(color_temp)


class FadeColor(FadeAmbient):
    def __init__(
        self,
        oh_fadetrigger_item_name,
        oh_fadeduration_item_name,
        oh_power_item_name,
        oh_dimmer_item_name,
        oh_temp_color_item_name,
        oh_color_item_name,
    ):
        super().__init__(
            oh_fadetrigger_item_name=oh_fadetrigger_item_name,
            oh_fadeduration_item_name=oh_fadeduration_item_name,
            oh_power_item_name=oh_power_item_name,
            oh_dimmer_item_name=oh_dimmer_item_name,
            oh_temp_color_item_name=oh_temp_color_item_name,
        )
        self.color_item = ColorItem.get_item(oh_color_item_name)
        self.fade_color_red = Fade(
            callback=self.fade_color_action, min_value=0, max_value=255
        )

        self.color_red_direction = "Red"
        self.color_green_direction = "Green"
        self.color_blue_direction = "Blue"

        logger.info("%s: FadeColor initialized.", oh_power_item_name)

    def fade_start(self, event):
        assert isinstance(event, ValueChangeEvent)
        logger.info("%s: Fading started.", self.power_item.name)
        min_step_duration = 5
        if self.duration_time / 10 < 10:
            min_step_duration = 2

        if self.color_red_direction == "Red":
            self.fade_color_red.setup(
                start_value=0,
                stop_value=255,
                duration=self.duration_time * 3.333333,
                min_step_duration=min_step_duration,
            )
        else:
            self.fade_color_red.setup(
                start_value=255,
                stop_value=0,
                duration=self.duration_time * 3.333333,
                min_step_duration=min_step_duration,
            )
        self.fade_color_red.schedule_fade()
        self.fade_color_action(0)
        super().fade_start(ValueChangeEvent(name="start", value=0, old_value=0))

    def fade_stop(self, event):
        assert isinstance(event, ValueChangeEvent)
        logger.info("%s: Fading stopped.", self.power_item.name)
        self.fade_color_red.stop_fade()
        super().fade_stop(ValueChangeEvent(name="stop", value=0, old_value=0))

    def fade_color_action(self, value):
        dimmer_value = int(self.fade_dimmer.get_value())
        color_temp = int(self.fade_temp_color.get_value())
        color_red = int(self.fade_color_red.get_value())
        logger.info(
            "%s: Fade value brightness: %d - color_temp: %d - color_red: %d",
            self.power_item.name,
            dimmer_value,
            color_temp,
            color_red,
        )

        if self.fade_color_red.is_finished:
            if self.dimmer_direction == "Red":
                self.dimmer_direction = "Black"
            else:
                self.dimmer_direction = "Red"
            self.fade_start(ValueChangeEvent(name="stop", value=0, old_value=0))

        self.color_item.post_rgb(color_red, 0, 0)


FadeDimmer(
    "LichtGrillbereich_FadeTrigger",
    "LichtGrillbereich_FadeDuration",
    "LichtGrillbereich_Power",
    "LichtGrillbereich_Helligkeit",
)

FadeAmbient(
    "Brunnen_FadeTrigger",
    "Brunnen_FadeDuration",
    "Brunnen_Power",
    "Brunnen_Brightness",
    "Brunnen_ColorTemp",
)

FadeColor(
    "FernseherLEDStrip_FadeTrigger",
    "FernseherLEDStrip_FadeDuration",
    "FernseherLEDStrip_Power",
    "FernseherLEDStrip_Brightness",
    "FernseherLEDStrip_Color_Temperature",
    "FernseherLEDStrip_Farbe",
)
