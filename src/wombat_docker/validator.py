#
# Title: validator.py
# Description: ensure valid hyena files
# Development Environment: Ubuntu 22.04.5 LTS/python 3.10.12
# Author: G.S. Cole (guycole at gmail dot com)
#
import logging
import datetime
import json
import os

from postgres import PostGres

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("hyena")

class Validator:

    def __init__(self, postgres: PostGres):
        self.postgres = postgres

        # path from inside docker container
        self.failure_dir = "/mnt/wombat/failure/"
        self.fresh_dir = "/mnt/wombat/fresh/hyena"
        self.success_dir = "/mnt/wombat/hyena/success/"

        # path for mac development
        # self.failure_dir = "/var/wombat/failure/"
        # self.fresh_dir = "/var/wombat/fresh/hyena"
        # self.success_dir = "/var/wombat/hyena/success/"

        self.failure = 0
        self.success = 0

    def file_failure(self, file_name: str):
        logger.info(f"file failure:{file_name}")

        self.failure += 1
        os.rename(file_name, self.failure_dir + file_name)

    def file_success(self, file_name: str):
        #logger.info(f"file success:{file_name}")

        self.success += 1
        os.rename(file_name, self.success_dir + "/" + file_name)

    def file_reader(self, file_name: str) -> bool:
        try:
            with open(file_name, "r", encoding="utf-8") as in_file:
                self.raw_buffer = json.load(in_file)
        except Exception as error:
            logger.error(f"file read failed for {file_name}: {error}")
            return False

        return True

    def load_log_test(self, test_file_name: str) -> bool:
        try:
            candidate = self.postgres.load_log_select_by_file_name(test_file_name)
            if candidate is not None:
                logger.info(f"skippping already processed:{test_file_name}")
                return False
            else:
                load_log = {
                    "epoch_seconds": self.raw_buffer["timeStamp"]["epochSeconds"],
                    "file_name": test_file_name,
                    "file_time": self.raw_buffer["timeStamp"]["iso8601"],
                    "load_time": datetime.datetime.now(),
                    "mode": self.raw_buffer["mode"],
                    "obs_quantity": len(self.raw_buffer["observations"]),
                    "platform": self.raw_buffer["equipment"]["platform"],
                    "project": self.raw_buffer["project"],
                }

                self.postgres.load_log_insert(load_log)

                return True
        except Exception as error:
            logger.error(f"postgres insert failed for {test_file_name}: {error}")        
        
        return False

    def file_processor(self, file_name: str) -> None:
        if os.path.isfile(file_name) is False:
            logger.warning(f"skipping non-file:{file_name}")
            self.file_failure(file_name)
            return

        if not self.file_reader(file_name):
            logger.warning(f"file read failed for {file_name}")
            self.file_failure(file_name)
            return

        if self.raw_buffer["version"] == 1 and self.raw_buffer["project"].startswith("hyena"):
            pass
        else:
            logger.warning(f"invalid version or project for {file_name}")
            self.file_failure(file_name)
            return
        
        if self.load_log_test(file_name):
            self.file_success(file_name)
        else:
            self.file_failure(file_name)

    def execute(self) -> None:
        logger.info("validator")
        logger.info(f"fresh dir:{self.fresh_dir}")

        os.chdir(self.fresh_dir)
        targets = sorted(os.listdir("."))
        logger.info(f"{len(targets)} files noted")

        for target in targets:
            logger.info(f"target:{target}")
            self.file_processor(target)

        logger.info(f"validator success:{self.success} failure:{self.failure}")

# ;;; Local Variables: ***
# ;;; mode:python ***
# ;;; End: ***
