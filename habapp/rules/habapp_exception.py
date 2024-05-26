"""send notifications to user if an exception occurs"""

import HABApp
from HABApp.core.events.habapp_events import HABAppException
from HABApp.core.events import EventFilter
from HABApp.util import RateLimiter
from HABApp.openhab.items import StringItem

import logging

# Set up rate limiter to limit the amount of notifications
LIMITER = RateLimiter("MyNotifications")
LIMITER.parse_limits("5 in 1 minute", algorithm="fixed_window_elastic_expiry")
LIMITER.parse_limits("20 in 1 hour", algorithm="leaky_bucket")

logger = logging.getLogger("Exceptions")


class NotifyOnError(HABApp.Rule):
    def __init__(self):
        super().__init__()

        # Listen to all errors
        self.listen_event("HABApp.Errors", self.on_error, EventFilter(HABAppException))
        logger.info("NotifyOnError initialized")

    def on_error(self, error_event: HABAppException):
        msg = (
            error_event.to_str()
            if isinstance(error_event, HABAppException)
            else error_event
        )

        # use limiter
        if not LIMITER.allow():
            return None

        # Replace this part with your notification logic
        logger.error("Error in rules:")
        logger.error(msg)
        oh_item = StringItem.get_item("HABApp_Exception")
        oh_item.oh_post_update(msg)


NotifyOnError()


# this is a faulty rule as an example. Do not create this part!
class FaultyRule(HABApp.Rule):
    def __init__(self):
        super().__init__()
        self.run.soon(self.faulty_function)

    def faulty_function(self):
        1 / 0


FaultyRule()
