"""check if all elements are part of the group as designed"""

# log:set INFO jsr223.jython.mp3_player_mode
# minimum version python-statemachine = 1.0.3
import logging  # required for extended logging

from datetime import time

import HABApp
from HABApp.openhab.items import ContactItem, SwitchItem, GroupItem, OpenhabItem

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

    def maintain_groups_daily(self):
        param_file = "maintain_groups"
        groups = HABApp.DictParameter(param_file, "Groups", default_value=None)
        for group in groups.values():
            self.handle_group(group)

    def handle_group(self, group_description):
        log.info("handling group %s", group_description)
        group_name = group_description["GroupName"]
        log.info("found group name %s", group_name)
        group_item_rules = group_description["MemberItemRule"]
        for selector, rule in group_item_rules.items():
            log.info("found rule %s:%s", selector, rule)

        for item in self.get_items(OpenhabItem):
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
            if "Name" in group_item_rules:
                if item.name == group_item_rules["Name"]:
                    log.info(
                        "   - item %s has Name %s", item.name, group_item_rules["Name"]
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
                    log.info(
                        "item %s matched rule(s) but is already in %s",
                        oh_item.name,
                        group_name,
                    )
                else:
                    log.info(
                        "item %s matched rule(s) but is not yet in %s",
                        oh_item.name,
                        group_name,
                    )
            else:
                if group_name in item.groups:
                    log.warning(
                        "item %s not matched rule(s) but is already in %s",
                        oh_item.name,
                        group_name,
                    )


maintain_groups()
