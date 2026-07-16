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

        self.failure_dir = os.environ.get("FAILURE_DIR", "/var/wombat/failure")
        self.fresh_dir = os.environ.get("FRESH_DIR", "/var/wombat/fresh/heeler")
        self.success_dir = os.environ.get("SUCCESS_DIR", "/var/wombat/heeler/success")

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
        logger.info(f"load_log_test for file: {test_file_name}")

        try:
            candidate = self.postgres.load_log_select_by_file_name(test_file_name)
            if candidate is None:
                logger.info(f"processing new file:{test_file_name}")

                geo_loc = self.postgres.geo_loc_select_by_site(self.raw_buffer["geoLoc"]["siteName"])
                if len(geo_loc) == 0:
                    logger.warning(
                        "must insert geo_loc for site: %s",
                        self.raw_buffer["geoLoc"]["siteName"],
                    )
                    return False

                load_log = {
                    "crate_name": self.raw_buffer["crateName"],
                    "epoch_seconds": self.raw_buffer["timeStamp"]["epochSeconds"],
                    "file_name": test_file_name,
                    "geo_loc_id": geo_loc[0].id,
                    "host_name": self.raw_buffer["equipment"]["hostName"],
                    "load_time": datetime.datetime.now(),
                    "mode": self.raw_buffer["job"]["mode"],

                    #"obs_quantity": len(self.raw_buffer["observations"]),
                    "obs_time": self.raw_buffer["timeStamp"]["iso8601"],
                    "site_name": self.raw_buffer["geoLoc"]["siteName"],
                    "task": self.raw_buffer["job"]["task"],
                }

                self.postgres.load_log_insert(load_log)

                if self.raw_buffer["job"]["mode"] == "dump1090":
                    quantity_adsb = len(self.raw_buffer["observations"])
                    quantity_uat = 0
                else:
                    quantity_adsb = 0
                    quantity_uat = len(self.raw_buffer["observations"])

                daily_score = {
                    "crate_name": self.raw_buffer["crateName"],
                    "file_quantity": 1,
                    "host_name": self.raw_buffer["equipment"]["hostName"],
                    "quantity_adsb": quantity_adsb,
                    "quantity_uat": quantity_uat,
                    "score_date": datetime.date.fromisoformat(self.raw_buffer["timeStamp"]["iso8601"][:10]),
                }

                self.postgres.daily_score_insert_or_update(daily_score)

                if len(self.raw_buffer["observations"]) < 1:
                    logger.info("skipping file with no observations")
                    return False

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

        if self.raw_buffer["version"] == 1 and self.raw_buffer["job"]["project"] == "hyena-v2":
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
            self.file_processor(target)

        logger.info(f"validator success:{self.success} failure:{self.failure}")

# ;;; Local Variables: ***
# ;;; mode:python ***
# ;;; End: ***
