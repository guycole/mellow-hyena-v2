#
# Title: collector_app.py
# Description: driver for hyena collector application
# Development Environment: Ubuntu 22.04.5 LTS/python 3.10.12
# Author: G.S. Cole (guycole at gmail dot com)
#
import logging
import os
import socket

import yaml
from yaml.loader import SafeLoader

from bootboy import BootBoy
from collector import Collector

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("hyena")


class CollectorApp:
    """Route collector component actions by stuntbox mode."""

    def __init__(self, stunt_box: str):
        self.stunt_box = stunt_box

    @staticmethod
    def _load_config(config_path: str) -> dict:
        with open(config_path, "r", encoding="utf-8") as in_file:
            configuration = yaml.load(in_file, Loader=SafeLoader)

        if not isinstance(configuration, dict):
            raise ValueError(f"invalid configuration object in {config_path}")

        return configuration

    def execute(self) -> int:
        logger.info("collector app execute: %s", self.stunt_box)

        if self.stunt_box == "collector":
            config_path = os.environ.get("COLLECTOR_CONFIG", "config.yaml")
            adsbex_key = os.environ.get("ADSBEX_KEY")
            configuration = self._load_config(config_path)
            collector = Collector(configuration)
            collector.execute(adsbex_key)
            return 0

        if self.stunt_box == "bootboy":
            target = os.environ.get("BOOTBOY_TARGET") or socket.gethostname()
            bootboy = BootBoy()
            bootboy.execute(target)
            return 0

        logger.error("invalid stunt_box option: %s", self.stunt_box)
        return 1


if __name__ == "__main__":
    stunt_box = os.environ.get("stuntbox", "collector")

    app = CollectorApp(stunt_box)
    raise SystemExit(app.execute())

# ;;; Local Variables: ***
# ;;; mode:python ***
# ;;; End: ***
