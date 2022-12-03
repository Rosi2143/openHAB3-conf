"""
This script uses a decorated cron rule that will generate logs every 10s
and can be used to test your initial setup.
"""

from core.rules import rule
from core.triggers import when


# description and tags are optional
@rule("Jython Hello World (cron decorators)", description="This is an example cron triggered rule using decorators", tags=["Test tag", "Hello World"])
@when("Time cron 0/10 * * * * ?")
def hello_world_cron_decorators(event):
    """
    prints Hello World

    Args:
        event (_type_): _description_
    """
    hello_world_cron_decorators.log.info("Hello World!")
