import logging  # required for extended logging

import HABApp
from HABApp.core.events import ValueUpdateEvent, ValueUpdateEventFilter, ValueChangeEvent, ValueChangeEventFilter
from HABApp.openhab.events import ItemStateEvent, ItemStateEventFilter, ItemCommandEvent, ItemCommandEventFilter, ItemStateChangedEvent, ItemStateChangedEventFilter
from HABApp.openhab.items import SwitchItem, ContactItem, DatetimeItem

log = logging.getLogger('MyRule')


class MyOpenhabRule(HABApp.Rule):
    """test rule for OpenHAB from the examples"""

    def __init__(self):
        """initialize OpenHAB testrule

        create items of all kinds and register callbacks for changes and updates"""
        super().__init__()

        # get items
        test_contact = ContactItem.get_item('HABApp_Contact')
        test_date_time = DatetimeItem.get_item('HABApp_DateTime')
        test_switch = SwitchItem.get_item('HABApp_Switch')

        # Trigger on item updates
        test_contact.listen_event(
            self.item_state_update, ItemStateEventFilter())
        test_date_time.listen_event(
            self.item_state_update, ValueUpdateEventFilter())

        # Trigger on item changes
        test_contact.listen_event(
            self.item_state_change, ItemStateChangedEventFilter())
        test_date_time.listen_event(
            self.item_state_change, ValueChangeEventFilter())

        # Trigger on item commands
        test_switch.listen_event(self.item_command, ItemCommandEventFilter())

    def item_state_update(self, event):
        """test update of state"""

        assert isinstance(event, ValueUpdateEvent)
        log.info('%s', event)

    def item_state_change(self, event):
        """test change of state"""

        assert isinstance(event, ValueChangeEvent)
        log.info('%s', event)

        # interaction is available through self.openhab or self.oh
        self.openhab.send_command('HABApp_Switch2', 'ON')

        # example for interaction with openhab item type
        switch_item = SwitchItem.get_item('HABApp_Switch')
        if switch_item.is_on():
            switch_item.off()
        else:
            switch_item.on()

    def item_command(self, event):
        """send a command ourselves"""

        assert isinstance(event, ItemCommandEvent)
        log.info('%s', event)

        # interaction is available through self.openhab or self.oh
        self.oh.post_update('HABApp_String', str(event))


# MyOpenhabRule()
