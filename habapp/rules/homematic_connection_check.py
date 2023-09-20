# https://habapp.readthedocs.io/en/latest/getting_started.html
import logging  # required for extended logging
import subprocess
import os
import re
from datetime import datetime, timedelta

import HABApp
from HABApp.openhab.items import StringItem

logger = logging.getLogger("HomematicConnect")

RASPBERRYMATIC_PI = "192.168.178.38"


class HomematicConnect(HABApp.Rule):
    """check if the Homematic is available on network"""

    def __init__(self):
        """initialize class"""
        super().__init__()

        self.ConnectionStatus = "INIT"
        self.uptime_last = 0
        self.uptime_item = StringItem.get_item("RaspiMaticGatewayExtras_Uptime")

        now_str = datetime.now().strftime("%Y.%m-%d %H:%M")
        logger.info("************************************************************")
        logger.info("************************************************************")
        logger.info("Start logger from script: %s", os.path.basename(__file__))
        logger.info("script started at %s", now_str)
        logger.info("************************************************************")
        logger.info("************************************************************")
        self.run.every(
            timedelta(seconds=5), timedelta(seconds=30), self.check_connection
        )
        self.run.every(timedelta(seconds=6), timedelta(minutes=6), self.check_uptime)

    def check_connection(self):
        res = 0
        now_str = datetime.now().strftime("%Y.%m-%d %H:%M")
        res = subprocess.run(["/bin/ping", "-c 1", RASPBERRYMATIC_PI], check=False)
        if res.returncode != 0:
            if self.ConnectionStatus != "NOK":
                self.ConnectionStatus = "NOK"
                logger.error("connection failed detected at %s", now_str)
        else:
            if self.ConnectionStatus != "OK":
                self.ConnectionStatus = "OK"
                logger.info("connection OK detected at %s", now_str)

    def check_uptime(self):
        uptime_state = self.uptime_item.get_value()
        p = re.match(r"(\d+)T\s(\d+):(\d+)", uptime_state)
        days = int(p.group(1))
        hours = int(p.group(2))
        minutes = int(p.group(3))
        logger.info("Uptime: --> %dTage %02dStunden %02dMinuten", days, hours, minutes)
        uptime_now = days * 24 * 60 + hours * 60 + minutes
        logger.info(
            "Compare Uptime\nUptime_last --> %d\nUptime_now  --> %d",
            self.uptime_last,
            uptime_now,
        )
        if self.uptime_last < uptime_now:
            logger.info("All is fine!")
        else:
            logger.warning("Restart homematic binding")
            res = subprocess.run(
                [
                    "whoami",
                ],
                capture_output=True,
                check=False,
            )
            logger.error(
                "whoami - %s",
                str(res.stdout, "UTF-8"),
            )
            res = subprocess.run(
                [
                    "/usr/bin/ssh",
                    "-p",
                    "8101",
                    "-i",
                    "/home/openhab/.ssh/karaf.id_rsa",
                    "openhab@localhost",
                    "bundle:restart",
                    "org.openhab.binding.homematic",
                ],
                capture_output=True,
                check=False,
            )
            if res.returncode != 0:
                logger.error(
                    "restart homematic binding failed - %d\nARGS: %s\nSTDOUT: %s\nSTDERR: %s",
                    res.returncode,
                    res.args,
                    str(res.stdout, "UTF-8"),
                    str(res.stderr, "UTF-8"),
                )
            else:
                logger.info("restart homematic binding success")
        self.uptime_last = uptime_now


# Rules
HomematicConnect()
