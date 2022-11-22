import logging

import HABApp
from HABApp.openhab.events import ItemStateChangedEvent
from HABApp.openhab.items import SwitchItem, ContactItem, OpenhabItem

log = logging.getLogger('ContactSwitch')

class ContactSwitchMapper(HABApp.Rule):
    """convert a contact to a swtich - as tinkerforge and homematic are incompatible"""

    def __init__(self):
        """initalize the class and create an element for all contact items with "_Contact_Switch" in the name."""

        super().__init__()

        # get items
        for item in self.get_items(OpenhabItem):
           log.debug( f"found item: {item.name}")
           if ("_Contact_Switch" in item.name):
              log.info( f"found item: {item.name}")
              contactName = (item.name).replace("_Switch","")
              my_contact = ContactItem.get_item(contactName)
              my_contact.listen_event(self.item_state_change, ItemStateChangedEvent)
              log.info( f"listen to item: {my_contact.name}")

    def item_state_change(self, event):
        """if the state of any of the element items changed to the mappping to switch."""
        assert isinstance(event, ItemStateChangedEvent)
        log.info( f'{event.name} changed to {event.value}')
        switch_item = SwitchItem.get_item((event.name)+"_Switch")
        if event.value == "OPEN":
            switch_item.on()
        else:
            switch_item.off()

ContactSwitchMapper()