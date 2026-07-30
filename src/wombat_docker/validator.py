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

from helper.json_helper import JsonHelper, schema

from helper.postgres import PostGres

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("validator")

class Validator:

    def __init__(self, postgres: PostGres):
        self.postgres = postgres

        self.failure_dir = os.environ.get("FAILURE_DIR", "/var/wombat/failure")
        self.fresh_dir = os.environ.get("FRESH_DIR", "/var/wombat/fresh/heeler")
        self.success_dir_adsb = os.environ.get("SUCCESS_DIR_ADSB", "/var/wombat/hyena/success_adsb")
        self.success_dir_uat = os.environ.get("SUCCESS_DIR_UAT", "/var/wombat/hyena/success_uat")

        self.failure = 0
        self.success_adsb = 0
        self.success_uat = 0

        self.adsb_flag = True

        self.jh = JsonHelper()

    def file_failure(self, file_name: str):
        logger.info(f"file failure:{file_name}")

        self.failure += 1
        os.rename(file_name, self.failure_dir + file_name)

    def file_success(self, file_name: str):
        #logger.info(f"file success:{file_name}")

        if self.adsb_flag:
            self.success_adsb += 1
            os.rename(file_name, self.success_dir_adsb + "/" + file_name)
        else:
            self.success_uat += 1
            os.rename(file_name, self.success_dir_uat + "/" + file_name)

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
                        self.jh.raw_json["geoLoc"]["siteName"],
                    )
                    return False

                load_log = {
                    "crate_name": self.jh.raw_json["crateName"],
                    "epoch_seconds": self.jh.raw_json["timeStamp"]["epochSeconds"],
                    "file_name": test_file_name,
                    "geo_loc_id": geo_loc[0].id,
                    "host_name": self.jh.raw_json["equipment"]["hostName"],
                    "load_time": datetime.datetime.now(),
                    "mode": self.jh.raw_json["job"]["mode"],
                    "obs_quantity": len(self.jh.raw_json["observations"]),
                    "obs_time": self.jh.raw_json["timeStamp"]["iso8601"],
                    "site_name": self.jh.raw_json["geoLoc"]["siteName"],
                    "task": self.jh.raw_json["job"]["task"],
                }

                self.postgres.load_log_insert(load_log)

                if self.jh.raw_json["job"]["mode"] == "dump1090":
                    self.adsb_flag = True
                    quantity_adsb = len(self.jh.raw_json["observations"])
                    quantity_uat = 0
                else:
                    self.adsb_flag = False
                    quantity_adsb = 0
                    quantity_uat = len(self.jh.raw_json["observations"])

                daily_score = {
                    "crate_name": self.jh.raw_json["crateName"],
                    "file_quantity": 1,
                    "host_name": self.jh.raw_json["equipment"]["hostName"],
                    "quantity_adsb": quantity_adsb,
                    "quantity_uat": quantity_uat,
                    "score_date": datetime.date.fromisoformat(self.jh.raw_json["timeStamp"]["iso8601"][:10]),
                }

                self.postgres.daily_score_insert_or_update(daily_score)

                if len(self.jh.raw_json["observations"]) < 1:
                    logger.info("skipping file with no observations")
                    return False

                return True
        except Exception as error:
            logger.error(f"postgres insert failed for {test_file_name}: {error}")        
        
        return False

    def file_processor(self, file_name: str) -> None:
        logger.info(f"processing file: {file_name}")

        if os.path.isfile(file_name) is False:
            logger.warning(f"skipping non-file:{file_name}")
            self.file_failure(file_name)
            return

        if not self.jh.json_file_reader(file_name, True):
            logger.warning(f"file read failed for {file_name}")
            self.file_failure(file_name)
            return

        try:
            if self.jh.raw_json["version"] == 1 and self.jh.raw_json["job"]["project"] == "hyena-v2":
                pass
            else:
                logger.warning(f"invalid version or project for {file_name}")
                self.file_failure(file_name)
                return
        except Exception as error:
            logger.error(f"project/version failure for {file_name}: {error}")
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

        logger.info(f"validator adsb success:{self.success_adsb} uat success:{self.success_uat} failure:{self.failure}")

# ;;; Local Variables: ***
# ;;; mode:python ***
# ;;; End: ***
