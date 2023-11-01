"""create uiSemantics Metadata for improved names in UI"""

# log:set INFO jsr223.jython.mp3_player_mode
# minimum version python-statemachine = 1.0.3
import logging  # required for extended logging
import yaml

import HABApp
from HABApp.openhab.items import SwitchItem, OpenhabItem
from HABApp.openhab.events import ItemStateUpdatedEvent, ItemStateUpdatedEventFilter

log = logging.getLogger("UiSemantics")

OH_CONF = "/etc/openhab/"
UI_NAMESPACE = "uiSemantics"


class create_ui_semantics(HABApp.Rule):
    """re-create the uiSemantics MetaData"""

    def __init__(self):
        """initialize the logger test"""
        super().__init__()

        self._log_indend = 0
        self._itemsAdded = []

        self.read_parameter("ui_semantics")

        trigger_switch = SwitchItem.get_item("HABApp_trigger_UISemantics")
        trigger_switch.listen_event(self.do_it, ItemStateUpdatedEventFilter())

        log.info("create_ui_semantics initialized")

    def read_parameter(self, param_file):
        self._prepositionDefaultString = HABApp.Parameter(
            param_file, "prepositionDefaultString", default_value=" in the "
        ).value
        log.info("prepositionDefaultString: %s", self._prepositionDefaultString)

        prepositionExtra = dict(
            HABApp.DictParameter(
                param_file, "prepositionExtra", default_value=None
            ).value
        )

        self._prepositionExtra = {}
        for key in prepositionExtra.keys():
            self._prepositionExtra[key] = {}
            self._prepositionExtra[key]["string"] = prepositionExtra[key]["string"]
            log.debug(
                "prepositionExtra - string:%s",
                yaml.dump(
                    prepositionExtra[key]["string"],
                    default_flow_style=False,
                    allow_unicode=True,
                ),
            )
            self._prepositionExtra[key]["locations"] = list(
                prepositionExtra[key]["locations"].keys()
            )
            log.debug(
                "prepositionExtra - location:\n%s",
                yaml.dump(
                    list(prepositionExtra[key]["locations"].keys()),
                    default_flow_style=False,
                    allow_unicode=True,
                ),
            )

        log.info(
            "prepositionExtra:\n%s",
            yaml.dump(
                self._prepositionExtra, default_flow_style=False, allow_unicode=True
            ),
        )

        self._uiSemanticsKeys = dict(
            HABApp.DictParameter(param_file, "uiSemanticsKeys", default_value=None)
        ).copy()
        log.info(
            "uiSemanticsKeys:\n%s",
            yaml.dump(
                self._uiSemanticsKeys, default_flow_style=False, allow_unicode=True
            ),
        )

    def do_it(self, event):
        assert isinstance(event, ItemStateUpdatedEvent)

        if event.value != "ON":
            return

        log.info("Starting: Collecting semantics")
        self._log_indend = 0
        self._itemsAdded = []
        self.read_parameter("ui_semantics")

        all_items = sorted(
            self.get_items(OpenhabItem), key=lambda x: x.name, reverse=False
        )
        self.num_of_all_items = len(all_items)
        self.item_counter = 0
        for item in all_items:
            self.item_counter += 1
            oh_item = self.openhab.get_item(item.name)
            self.logItemInfo(oh_item, False)
            self.enrichMetadata(oh_item)

        for new_item in self._itemsAdded:
            log.debug("added: %s", new_item)
        log.info("Added %d uiSemantics", len(self._itemsAdded))

        remove_count = 0
        for item in self.get_items(OpenhabItem):
            self.logItemInfo(item, True)
            if self.getMetadata(item, UI_NAMESPACE) is not None:
                log.debug("found in Registry: %s", item.name)
                if item.name in self._itemsAdded:
                    log.debug("keep item")
                else:
                    remove_count += 1
                    log.info("(%d): remove item %s", remove_count, item.name)
        #                    MetadataRegistry.remove(new MetadataKey(UI_NAMESPACE, item.getUID().getItemName()))
        log.info("Done: Collecting semantics")

    def logItemInfo(self, p_oh_item, p_logMetaData):
        log.debug("found in Registry item: %s", p_oh_item)
        log.debug("found in Registry name: %s", p_oh_item.name)
        if p_logMetaData:
            metaData = p_oh_item.metadata
            log.debug("found in Registry NameSpaces: %s", metaData.keys())

    def enrichMetadata(self, p_oh_item, p_icon=None):
        log.info(
            "enrich item(%d/%d): %s - %s",
            self.item_counter,
            self.num_of_all_items,
            p_oh_item.name,
            p_oh_item.label,
        )
        isPointOf = self.getRelationItem(p_oh_item, "semantics", "isPointOf")

        if isPointOf is not None:
            log.debug("Item %s isPointOf: %s", p_oh_item, isPointOf.name)
            equipmentItem = isPointOf
        else:
            log.debug("no equipmentItem found. Setting it to %s", p_oh_item.name)
            equipmentItem = p_oh_item

        hasLocationItem = self.getRelationItem(
            equipmentItem, "semantics", "hasLocation"
        )
        if hasLocationItem is not None:
            log.debug(
                "EquipmentItem %s hasLocation: %s",
                equipmentItem.name,
                hasLocationItem.name,
            )

        metaEquipmentItem = None
        if hasLocationItem is None:
            safetyCounter = 0
            while (
                (metaEquipmentItem is None)
                and (hasLocationItem is None)
                and (safetyCounter < 5)
            ):
                safetyCounter = safetyCounter + 1
                metaEquipmentItem = self.getRelationItem(
                    equipmentItem, "semantics", "isPartOf"
                )

                if metaEquipmentItem is not None:
                    log.debug(
                        "%d:  %s is part of: %s",
                        safetyCounter,
                        equipmentItem.name,
                        metaEquipmentItem.name,
                    )

                    hasLocationItem = self.getRelationItem(
                        metaEquipmentItem, "semantics", "hasLocation"
                    )
                    if hasLocationItem is not None:
                        log.debug(
                            "metaEquipmentItem %s hasLocation: %s",
                            metaEquipmentItem.name,
                            hasLocationItem.name,
                        )
                    else:
                        log.debug(
                            "metaEquipmentItem %s has no Location",
                            metaEquipmentItem.name,
                        )

        if (hasLocationItem is not None) and (hasLocationItem is not None):
            self._uiSemanticsKeys["equipment"] = equipmentItem.label
            self._uiSemanticsKeys["equipmentItem"] = equipmentItem.name
            self._uiSemanticsKeys["location"] = hasLocationItem.label
            found_preposition = False
            for key in self._prepositionExtra.keys():
                if (
                    self._uiSemanticsKeys["location"]
                    in self._prepositionExtra[key]["locations"]
                ):
                    self._uiSemanticsKeys["preposition"] = self._prepositionExtra[key][
                        "string"
                    ]
                    found_preposition = True

            if not found_preposition:
                self._uiSemanticsKeys["preposition"] = self._prepositionDefaultString

            self._uiSemanticsKeys["icon"] = p_icon

            self._uiSemanticsKeys["fail"] = int(self._uiSemanticsKeys["warn"]) * 1.5

            if (
                self.getRelationItem(p_oh_item, UI_NAMESPACE, "equipmentItem")
                is not None
            ):
                log.info(
                    "Item: '%s' UPDATE Metadata in %s: %s%s%s",
                    p_oh_item.name,
                    UI_NAMESPACE,
                    self._uiSemanticsKeys["equipment"],
                    self._uiSemanticsKeys["preposition"],
                    self._uiSemanticsKeys["location"],
                )
                self._itemsAdded.append(p_oh_item.name)
                # MetadataRegistry.update(new Metadata(new MetadataKey(UI_NAMESPACE, oh_item), None, self.uiSemanticsKeys))
            else:
                log.info(
                    "Item: '%s' ADD Metadata in %s: %s%s%s",
                    p_oh_item.name,
                    UI_NAMESPACE,
                    self._uiSemanticsKeys["equipment"],
                    self._uiSemanticsKeys["preposition"],
                    self._uiSemanticsKeys["location"],
                )
                self._itemsAdded.append(p_oh_item.name)
                # MetadataRegistry.add(new Metadata(new MetadataKey(UI_NAMESPACE, oh_item), None, self.uiSemanticsKeys))

        return None

    def getRelationItem(self, p_oh_item, p_semantic, p_relation):
        self._log_indend += 2
        log.info(
            "%sgetRelationItem[in]: %s - with semantic '%s' - has relation: '%s'",
            " " * self._log_indend,
            p_oh_item.name,
            p_semantic,
            p_relation,
        )

        semantics = self.getMetadata(p_oh_item, p_semantic)
        hasRelation = None
        relationItem = None
        log.debug(
            "%ssemantics --> %s:%s", " " * self._log_indend, p_semantic, semantics
        )
        if semantics is not None:
            hasRelation = self.getRelation(semantics, p_relation)
            log.debug(
                "%shasRelation --> %s:%s",
                " " * self._log_indend,
                p_relation,
                hasRelation,
            )
            if hasRelation is not None:
                if self.openhab.item_exists(hasRelation):
                    relationItem = self.openhab.get_item(hasRelation)
                    # log.debug(relationItem)
                    log.info(
                        "%s> getRelationItem[out]: %s -> %s -> %s",
                        "-" * self._log_indend,
                        p_oh_item.name,
                        p_relation,
                        relationItem.name,
                    )
                else:
                    hasRelation = None
            else:
                log.debug(
                    "%sgetRelationItem[out]: No relation found in Model! - %s",
                    " " * self._log_indend,
                    hasRelation,
                )
        else:
            log.debug(
                "%sgetRelationItem[out]: No semantic found in Model!",
                " " * self._log_indend,
            )

        self._log_indend = self._log_indend - 2
        return relationItem

    def getMetadata(self, p_oh_item, p_namespace):
        metaData = p_oh_item.metadata
        if p_namespace in metaData.keys():
            return metaData[p_namespace]
        else:
            return None

    def getRelation(self, p_metaData, p_relation):
        config = "config"
        if config not in p_metaData.keys():
            return None
        if p_relation in p_metaData[config].keys():
            return p_metaData[config][p_relation]
        else:
            return None


create_ui_semantics()
