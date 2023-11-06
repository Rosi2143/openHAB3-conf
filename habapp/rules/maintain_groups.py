"""check if all elements are part of the group as designed"""

# log:set INFO jsr223.jython.mp3_player_mode
# minimum version python-statemachine = 1.0.3
import logging  # required for extended logging

from datetime import time

import HABApp
from HABApp.openhab.items import OpenhabItem

log = logging.getLogger("MaintainGroup")

OH_CONF = "/etc/openhab/"


class maintain_groups(HABApp.Rule):
    """check all groups for missing/extra items"""

    def __init__(self):
        """initialize the logger test"""
        super().__init__()

        self.run.soon(callback=self.maintain_groups_daily)
        self.run.on_every_day(time=time(0), callback=self.maintain_groups_daily)
        log.info("maintain groups started")
        self.items_changed = 0
        self.items_not_changed = 0
        self.items_removed = 0

    def maintain_groups_daily(self):
        param_file = "maintain_groups"
        groups = HABApp.DictParameter(param_file, "Groups", default_value=None)
        self.items_changed = 0
        self.items_not_changed = 0
        self.items_removed = 0
        for group in groups.values():
            self.handle_group(group)
        log.info("##################################")
        log.info("Result overall")
        log.info("Number of groups  = %d", len(groups.values()))
        log.info("Items changed     = %s", self.items_changed)
        log.info("Items not changed = %s", self.items_not_changed)
        log.info("Items removed     = %s", self.items_removed)
        log.info("maintain groups done")

    def handle_group(self, group_description):
        log.info("handling group %s", group_description)
        group_name = group_description["GroupName"]
        log.info("found group name %s", group_name)
        if not self.openhab.item_exists(group_name):
            log.error("Group does not exist")
            return
        group_item_rules = group_description["MemberItemRule"]
        for selector, rule in group_item_rules.items():
            log.info("found rule %s:%s", selector, rule)

        exception_list = []
        if "Exception" in group_description:
            exception_list = list(group_description["Exception"].keys())
            log.info("exception list :%s", exception_list)

        items_changed = 0
        items_not_changed = 0
        items_removed = 0
        for item in sorted(
            self.get_items(OpenhabItem), key=lambda x: x.name, reverse=False
        ):
            oh_item = self.openhab.get_item(item.name)
            found = True
            if "Label" in group_item_rules:
                if item.label == group_item_rules["Label"]:
                    log.info(
                        "   - item %s has Label %s",
                        item.name,
                        group_item_rules["Label"],
                    )
                    found = found and True
                else:
                    found = False
            if "is_Name" in group_item_rules:
                if item.name == group_item_rules["is_Name"]:
                    log.info(
                        "   - item %s has Name %s",
                        item.name,
                        group_item_rules["is_Name"],
                    )
                    found = found and True
                else:
                    found = False
            if "in_Name" in group_item_rules:
                if group_item_rules["in_Name"] in item.name:
                    log.info(
                        "   - item %s contains %s",
                        item.name,
                        group_item_rules["in_Name"],
                    )
                    found = found and True
                else:
                    found = False
            if "Tag" in group_item_rules:
                if group_item_rules["Tag"] in oh_item.tags:
                    log.info(
                        "   - item %s has Tag %s", item.name, group_item_rules["Tag"]
                    )
                    found = found and True
                else:
                    found = False
            if "Type" in group_item_rules:
                if oh_item.type == group_item_rules["Type"]:
                    log.info(
                        "   - item %s has Type %s", item.name, group_item_rules["Type"]
                    )
                    found = found and True
                else:
                    found = False
            if found:
                if group_name in item.groups:
                    if oh_item.name in exception_list:
                        self.remove_item_from_group(
                            oh_item=oh_item, group_name=group_name
                        )
                        items_removed += 1
                    else:
                        log.info(
                            "item %s matched rule(s) but is already in %s",
                            oh_item.name,
                            group_name,
                        )
                        items_not_changed += 1
                else:
                    if oh_item.name in exception_list:
                        items_not_changed += 1
                    else:
                        self.add_item_to_group(oh_item=oh_item, group_name=group_name)
                        items_changed += 1
            else:
                if group_name in item.groups:
                    self.remove_item_from_group(oh_item=oh_item, group_name=group_name)
                    items_removed += 1

        log.info("Result for group %s", group_name)
        log.info("Items changed     = %s", items_changed)
        log.info("Items not changed = %s", items_not_changed)
        log.info("Items removed     = %s", items_removed)
        self.items_changed += items_changed
        self.items_not_changed += items_not_changed
        self.items_removed += items_removed

    def add_item_to_group(self, oh_item, group_name):
        log.info("Add item %s to group %s", oh_item.name, group_name)
        item_groups = list(oh_item.groups)
        item_groups.append(group_name)
        if not self.openhab.create_item(
            item_type=oh_item.type,
            name=oh_item.name,
            label=oh_item.label,
            category=oh_item.category,
            tags=list(oh_item.tags),
            groups=item_groups,
        ):
            log.error("item update failed")
            log.error("name     = %s", oh_item.name)
            log.error("label    = %s", oh_item.label)
            log.error("tags     = %s", oh_item.tags)
            log.error("category = %s", oh_item.category)
            log.error("groups   = %s --> %s", oh_item.groups, type(oh_item.groups))
            log.error("metadata = %s", oh_item.metadata)
        else:
            log.info("item update succeeded")

    def remove_item_from_group(self, oh_item, group_name):
        log.warning("Remove item %s from group %s", oh_item.name, group_name)
        item_groups = list(oh_item.groups)
        item_groups.remove(group_name)
        if not self.openhab.create_item(
            item_type=oh_item.type,
            name=oh_item.name,
            label=oh_item.label,
            category=oh_item.category,
            tags=list(oh_item.tags),
            groups=item_groups,
        ):
            log.error("item update failed")
            log.error("name     = %s", oh_item.name)
            log.error("label    = %s", oh_item.label)
            log.error("tags     = %s", oh_item.tags)
            log.error("category = %s", oh_item.category)
            log.error("groups   = %s --> %s", oh_item.groups, type(oh_item.groups))
            log.error("metadata = %s", oh_item.metadata)
        else:
            log.info("item update succeeded")


maintain_groups()
