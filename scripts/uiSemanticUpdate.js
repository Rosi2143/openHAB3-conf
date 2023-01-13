// log:set debug org.openhab.model.script.Rules.Experiments

var logger = Java.type("org.slf4j.LoggerFactory").getLogger("org.openhab.model.script.Rules.Experiments")

var UI_NAMESPACE = "uiSemantics"
var FrameworkUtil = Java.type("org.osgi.framework.FrameworkUtil")
var _bundle = FrameworkUtil.getBundle(scriptExtension.class)
var bundle_context = _bundle.getBundleContext()
var MetadataRegistry_Ref = bundle_context.getServiceReference("org.openhab.core.items.MetadataRegistry")
var MetadataRegistry = bundle_context.getService(MetadataRegistry_Ref)
var MetadataKey = Java.type("org.openhab.core.items.MetadataKey")
var Metadata = Java.type("org.openhab.core.items.Metadata")

var itemsAdded = []
var prepositionFor = ["Küche", "Werkstatt", "Waschküche", "Bibliothek", "Garage", "Haustür", "Kammer"]
var uiSemanticsKeys = { "equipment": "", "equipmentItem": "", "location": "", "preposition": "", "icon": "", "warn": -30, "fail": -45 }

function getMetadata(itemName, namespace) {
    return MetadataRegistry.get(new MetadataKey(namespace, itemName))
}

var getValue = function (item, semantic, relation) {
    logger.info("getValue[in]: " + item + " - " + semantic + " - " + " with " + relation)

    var semantics = getMetadata(item, semantic)
    logger.debug(semantic + ":" + semantics)
    if ((semantics !== undefined) && (semantics !== null)) {
        var hasRelation = semantics.configuration[relation]
        logger.debug(relation + ":" + hasRelation)
        if ((hasRelation !== undefined) && (hasRelation !== null)) {
            var relationItem = ir.getItem(hasRelation)
            logger.debug(relationItem)
            logger.debug("getValue[out]: " + item + " -> " + relation + " -> " + relationItem.getName())
        }
        else {
            logger.info("getValue[out]: No relation found in Model! - " + hasRelation)
        }
    }
    else {
        logger.info("getValue[out]: No semantic found in Model!")
    }

    return ((hasRelation === undefined) || (hasRelation === null)) ? null : relationItem.getName()
}

var enrichMetadata = function (item, icon) {

    logger.info("enrich item: " + item)
    var isPointOf = getValue(item, "semantics", "isPointOf")
    logger.debug("Item " + item + " isPointOf: " + isPointOf)

    if (isPointOf !== null) {
        var equipmentItem = isPointOf === undefined ? ir.getItem(item) : ir.getItem(isPointOf)
        logger.debug("equipmentItem found: " + equipmentItem.name)
    } else {
        logger.debug("no equipmentItem found. Setting it to " + item)
        equipmentItem = ir.getItem(item)
    }

    var hasLocation = getValue(equipmentItem.name, "semantics", "hasLocation")
    logger.debug("EquipmentItem " + equipmentItem.name + " hasLocation: " + hasLocation)

    if (hasLocation === null) {
        var metaEquipment = "none"
        var safetyCounter = 0
        hasLocation = "none"
        while ((metaEquipment !== null) && (hasLocation !== null) && (safetyCounter < 5)) {
            metaEquipment = getValue(equipmentItem.name, "semantics", "isPartOf")
            logger.debug(safetyCounter + ": Equipment " + equipmentItem.name + " is part of: " + metaEquipment)
            safetyCounter = safetyCounter + 1

            if (metaEquipment !== null) {
                var metaEquipmentItem = metaEquipment === undefined ? ir.getItem(equipmentItem.name) : ir.getItem(metaEquipment)
                logger.debug("metaEquipmentItem found: " + metaEquipmentItem.name)

                hasLocation = getValue(metaEquipmentItem.name, "semantics", "hasLocation")
                logger.debug("metaEquipmentItem " + metaEquipmentItem.name + " hasLocation: " + hasLocation)
            }
        }
    }

    if ((hasLocation !== null) && (metaEquipment !== null)) {

        var locationItem = hasLocation === undefined ? ir.getItem(equipmentItem.name) : ir.getItem(hasLocation)

        uiSemanticsKeys.equipment = equipmentItem.label
        uiSemanticsKeys.equipmentItem = equipmentItem.name
        uiSemanticsKeys.location = locationItem.label
        uiSemanticsKeys.preposition = (prepositionFor.indexOf(uiSemanticsKeys.location) > -1) ? " in der " : " im "
        uiSemanticsKeys.icon = icon

        var warnTimeoutFor = { "LUMITH": -720, "SHELLYDW": -240, "SHELLYFLOOD": -1440 }
        for (var s in warnTimeoutFor) {
            if (item.toUpperCase().indexOf(s) > -1) {
                uiSemanticsKeys.warn = warnTimeoutFor[s]
                break
            }
        }
        uiSemanticsKeys.fail = uiSemanticsKeys.warn * 1.5

        if (getValue(item, UI_NAMESPACE, "equipmentItem") !== null) {
            logger.info("Item: " + item + " UPDATE Metadata in " + UI_NAMESPACE + ": " + uiSemanticsKeys.equipment + uiSemanticsKeys.preposition + uiSemanticsKeys.location)
            itemsAdded.push(item)
            MetadataRegistry.update(new Metadata(new MetadataKey(UI_NAMESPACE, item), null, uiSemanticsKeys))
        } else {
            logger.info("Item: " + item + " ADD Metadata in " + UI_NAMESPACE + ": " + uiSemanticsKeys.equipment + uiSemanticsKeys.preposition + uiSemanticsKeys.location)
            itemsAdded.push(item)
            MetadataRegistry.add(new Metadata(new MetadataKey(UI_NAMESPACE, item), null, uiSemanticsKeys))
        }
    }

    return null
}

function logItemInfo(item, metaItem) {
    logger.debug("found in Registry item: " + item)
    logger.debug("found in Registry UID: " + item.getUID())
    if (metaItem) {
        logger.debug("found in Registry NameSpace: " + item.getUID().getNamespace())
        logger.debug("found in Registry ItemName: " + item.getUID().getItemName())
    }
}

logger.info("Starting: Collecting semantics for 'main_widget'...")

var itemList = ir.getItems()
for each(var item in itemList) {
    logItemInfo(item, false)
    enrichMetadata(item.name)
}

for each(var item in itemsAdded) {
    logger.debug("added: " + item)
}

for each(var item in MetadataRegistry.getAll()) {
    logItemInfo(item, true)
    if (item.getUID().getNamespace() == UI_NAMESPACE) {
        logger.debug("found in Registry: " + item)
        if (itemsAdded.indexOf(item.getUID().getItemName()) > -1) {
            logger.debug("keep item")
        }
        else {
            logger.info("remove item" + item.getUID().getItemName())
            MetadataRegistry.remove(new MetadataKey(UI_NAMESPACE, item.getUID().getItemName()))
        }
    }
}

logger.info("Done: Collecting semantics for 'main_widget'...")
