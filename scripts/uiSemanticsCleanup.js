var logger = Java.type("org.slf4j.LoggerFactory").getLogger("org.openhab.model.script.Rules.Experiments");

var UI_NAMESPACE = "uiSemantics";
var FrameworkUtil = Java.type("org.osgi.framework.FrameworkUtil");
var _bundle = FrameworkUtil.getBundle(scriptExtension.class);
var bundle_context = _bundle.getBundleContext()
var MetadataRegistry_Ref = bundle_context.getServiceReference("org.openhab.core.items.MetadataRegistry");
var MetadataRegistry = bundle_context.getService(MetadataRegistry_Ref);
var MetadataKey = Java.type("org.openhab.core.items.MetadataKey");
var Metadata = Java.type("org.openhab.core.items.Metadata");

logger.info("Starting: removing all elements for " + UI_NAMESPACE + "...")

for each(var item in MetadataRegistry.getAll()) {
    logger.info("remove item" + item.getUID().getItemName())
    MetadataRegistry.remove(new MetadataKey(UI_NAMESPACE, item.getUID().getItemName()))
}
