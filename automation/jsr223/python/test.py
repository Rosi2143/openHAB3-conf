"""
test rule
"""
from core.rules import rule
from core.triggers import when
from core.log import logging, LOG_PREFIX


@rule("TestRule", description="Test Jython Rules", tags=["Tag 1", "Tag 2"])
@when("Time cron 0/10 * * * * ?")
@when("Item openHAB2Server_ItemLightGroundFloorGastWC received update")
def my_rule_function(event):
    my_rule_function.log.info("Hello World ----!")

    for item in ir.getAll():
        if item.name == "openHAB2Server_ItemLightGroundFloorGastWC":
            my_rule_function.log.info("List Item - name: [{}]".format(item))
            my_rule_function.log.info(
                "List Item - name: [{}]".format(item.getName()))
            my_rule_function.log.info(
                "List Item - type: [{}]".format(item.getType()))
            my_rule_function.log.info(
                "List Item - state: [{}]".format(item.getState()))
            my_rule_function.log.info(
                "List Item - label: [{}]".format(item.getLabel()))
            my_rule_function.log.info(
                "List Item - category: [{}]".format(item.getCategory()))
            my_rule_function.log.info(
                "List Item - tags: [{}]".format(item.getTags()))
            my_rule_function.log.info(
                "List Item - groups: [{}]".format(item.getGroupNames()))

    # logging.debug(
    #     "Logging example from root logger [DEBUG]: [{}]".format(5 + 5))
    # logging.info("Logging example from root logger [INFO]: [{}]".format(6 + 6))
    # logging.warning(
    #     "Logging example from root logger [WARN]: [{}]".format(7 + 7))
    # logging.error(
    #     "Logging example from root logger [ERROR]: [{}]".format(8 + 8))
    # logging.critical(
    #     "Logging example from root logger [TRACE]: [{}]".format(5 + 5))

    # logging.getLogger("{}.test_logging_script".format(LOG_PREFIX)).info(
    #     "Logging example from logger, using text appended to LOG_PREFIX: [{}]".format(5 + 5))

    # log = logging.getLogger("{}.test_logging_script".format(LOG_PREFIX))
    # log.info(
    #     "Logging example from logger, using text appended to LOG_PREFIX: [{}]".format(5 + 5))
