import logging  # required for extended logging

import HABApp
from HABApp.openhab.events import ItemStateChangedEvent
from HABApp.openhab.items import SwitchItem, ContactItem, OpenhabItem

log = logging.getLogger('ContactSwitch')


class ContactSwitchMapper(HABApp.Rule):
    """convert a contact to a switch - as tinkerforge and homematic are incompatible"""

    def __init__(self):
        """initialize the class and create an element for all contact items
        with "_Contact_Switch" in the name."""

        super().__init__()

        # get items
        for item in self.get_items(OpenhabItem):
            log.debug("found item: %s", item.name)
            if "_Contact_Switch" in item.name:
                log.info("found item: %s", item.name)
                contact_name = (item.name).replace("_Switch", "")
                my_contact = ContactItem.get_item(contact_name)
                my_contact.listen_event(
                    self.item_state_change, ItemStateChangedEvent)
                log.info("listen to item: %s", my_contact.name)
        log.info('rule ContactSwitchMapper started')

    def item_state_change(self, event):
        """if the state of any of the element items changed to the mapping to switch."""
        assert isinstance(event, ItemStateChangedEvent)
        log.info('%s changed to %s', event.name, event.value)
        switch_item = SwitchItem.get_item((event.name) + "_Switch")
        if event.value == "OPEN":
            switch_item.on()
        else:
            switch_item.off()


ContactSwitchMapper()
