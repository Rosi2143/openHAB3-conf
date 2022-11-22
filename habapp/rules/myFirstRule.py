# https://habapp.readthedocs.io/en/latest/getting_started.html
import logging

import HABApp
from HABApp.core.items import Item
from HABApp.core.events import ValueUpdateEvent, ValueUpdateEventFilter, ValueChangeEvent, ValueChangeEventFilter

logger = logging.getLogger('MyRule')

# Rules are classes that inherit from HABApp.Rule
class MyFirstRule(HABApp.Rule):
    """test rule for OpenHAB from the examples"""

    def __init__(self):
        """initialize the logger test"""
        super().__init__()

        # Use run.at to schedule things directly after instantiation,
        # don't do blocking things in __init__
        self.run.soon(self.say_something)

        logger.debug('Debug Message')
        logger.info('Info Message')
        logger.warning('Warning Message')
        logger.error('Error Message')

        logger.info('rule MyFirstRule started')

    def say_something(self):
        """print another log message to test the callbacks"""
        
        logger.info('That was easy! -')

class MyFirstRule2(HABApp.Rule):
    """test rule for OpenHAB from the examples"""

    def __init__(self, my_parameter):
        """initialize the test to trigger a delayed callback"""
        super().__init__()
        ## passed parameter
        self.param = my_parameter

        self.run.soon(self.say_something2)

    def say_something2(self):
        """log something to show that the callback works"""

        logger.info(f'Param {self.param}')


class MyFirstRule3(HABApp.Rule):
    """test rule for OpenHAB from the examples"""

    def __init__(self):
        """initialize the test for string items"""
        super().__init__()
        ## Get the item or create it if it does not exist
        self.my_item = Item.get_create_item('HABApp_String_')

        self.run.soon(self.say_something)

    def say_something(self):
        """use class elements in callback"""

        # Post updates to the item through the internal event bus
        self.my_item.post_value('Test')
        self.my_item.post_value('Change')

        # The item value can be used in comparisons through this shortcut ...
        if self.my_item == 'Change':
            logger.info('Item value is "Change"')
        # ... which is the same as this:
        if self.my_item.value == 'Change':
            logger.info('Item.value is "Change"')

class MyFirstRule4(HABApp.Rule):
    """test rule for OpenHAB from the examples"""

    def __init__(self):
        """initialize the test to pass parameter to callback-"""
        super().__init__()
        ## Get the item or create it if it does not exist
        self.my_item = Item.get_create_item('HABApp_String_')

        # Run this function whenever the item receives an ValueUpdateEvent
        self.listen_event(self.my_item, self.item_updated, ValueUpdateEventFilter())

        # Run this function whenever the item receives an ValueChangeEvent
        self.listen_event(self.my_item, self.item_changed, ValueChangeEventFilter())

        # If you already have an item you can use the more convenient method of the item
        self.my_item.listen_event(self.item_changed, ValueChangeEventFilter())

    # the function has 1 argument which is the event
    def item_changed(self, event: ValueChangeEvent):
        """callback for a specific event: ValueChangeEvent"""

        logger.info(f'{event.name} changed from "{event.old_value}" to "{event.value}"')
        logger.info(f'Last change of {self.my_item.name}: {self.my_item.last_change}')

    def item_updated(self, event: ValueUpdateEvent):
        """callback for a specific event: ValueUpdateEvent"""

        logger.info(f'{event.name} updated value: "{event.value}"')
        logger.info(f'Last update of {self.my_item.name}: {self.my_item.last_update}')

# Rules
MyFirstRule()

# This is normal python code, so you can create Rule instances as you like
for i in range(2):
    MyFirstRule2(i)
for t in ['Text 1', 'Text 2']:
    MyFirstRule2(t)

MyFirstRule4()

MyFirstRule3()
