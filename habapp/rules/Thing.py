import logging  # required for extended logging

from HABApp import Rule
from HABApp.openhab.events import ThingStatusInfoChangedEvent
from HABApp.openhab.items import Thing
from HABApp.core.events import EventFilter
from HABApp.openhab.items import GroupItem

log = logging.getLogger("Things")


class ThingsRule(Rule):
    """test rule for OpenHAB from the examples"""

    def __init__(self):
        """initialize OpenHAB testrule

        create items of all kinds and register callbacks for changes and updates"""
        super().__init__()

        thing_group_item = GroupItem.get_item("gThingItems")
        thing_list = sorted(self.get_items(Thing), key=lambda x: x.name, reverse=False)
        log.info(type(thing_list))
        for thing in thing_list:
            log.info("found %s : %s -> %s", thing.name, thing.label, thing.status)
            thing.listen_event(
                self.thing_status_changed,
                EventFilter(ThingStatusInfoChangedEvent),
                itemname=thing.label,
            )
            if not self.openhab.item_exists(thing.label):
                log.info("%s does not exist - continue", thing.label)
                continue

            _item = self.openhab.get_item(thing.label)
            _item_groups = list(_item.groups)

            if thing_group_item.name in _item_groups:
                log.info("%s already in %s", _item_groups, thing_group_item.name)
            else:
                _item_groups.append(thing_group_item.name)

                log.info("Adding %s to %s", _item.name, thing_group_item.name)

                if not self.openhab.create_item(
                    item_type="Group",
                    name=_item.name,
                    label=_item.label,
                    category=_item.category,
                    tags=list(_item.tags),
                    groups=_item_groups,
                ):
                    log.error("item update failed")
                    log.error("name     = %s", _item.name)
                    log.error("label    = %s", _item.label)
                    log.error("tags     = %s", _item.tags)
                    log.error("category = %s", _item.category)
                    log.error("groups   = %s --> %s", _item.groups, type(_item.groups))
                    log.error("metadata = %s", _item.metadata)
                else:
                    log.info("item update succeeded")

    def thing_status_changed(self, event: ThingStatusInfoChangedEvent, itemname=None):
        log.info(
            "%s : %s changed from %s to %s",
            event.name,
            itemname,
            event.old_status,
            event.status,
        )


ThingsRule()
