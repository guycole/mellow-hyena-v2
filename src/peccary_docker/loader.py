#
# Title: loader.py
# Description: load heeler files
# Development Environment: Ubuntu 22.04.5 LTS/python 3.10.12
# Author: G.S. Cole (guycole at gmail dot com)
#
import logging
import datetime
import json
import os

#from collector import adsb_exchange
from helper.json_helper import JsonHelper, schema

from helper.postgres import PostGres

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("loader")


class Loader:

    def __init__(self, postgres: PostGres):
        self.postgres = postgres

        self.failure_dir = os.environ.get("FAILURE_DIR", "/var/peccary/hyena/failure")
        self.fresh_dir = os.environ.get("FRESH_DIR", "/var/peccary/hyena/hyena-v2")

        self.failure = 0
        self.success = 0

        self.jh = JsonHelper()

    def file_failure(self, file_name: str):
        #        logger.info(f"file failure:{file_name}")

        self.failure += 1
        os.rename(file_name, self.failure_dir + "/" + file_name)

    def file_success(self, file_name: str):
        #        logger.info(f"file success:{file_name}")

        self.success += 1
        os.remove(file_name)

    def load_log_test(self, test_file_name: str) -> bool:
        logger.info(f"load_log_test for file: {test_file_name}")

        try:
            candidate = self.postgres.load_log_select_by_file_name(test_file_name)
            if candidate is None:
                logger.info(f"processing new file:{test_file_name}")

                geo_loc = self.postgres.geo_loc_select_by_site(self.jh.raw_json["geoLoc"]["siteName"])
                if len(geo_loc) == 0:
                    logger.warning(
                        "must insert geo_loc for site: %s",
                        self.jh.raw_json["geoLoc"]["siteName"],
                    )
                    return False

                load_log = {
                    "adsbex_quantity": len(self.jh.raw_json["adsbex"]),
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

                self.load_log_id = self.postgres.load_log_insert(load_log).id

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

    def load_adsbex(self) -> bool:
        try:
            adsbex = self.jh.raw_json["adsbex"]
            for kk, vv in adsbex.items():
                adsbex_args = {
                    "adsb_hex": vv["adsb_hex"],
                    "category": vv["category"],
                    "emergency": vv["emergency"],
                    "flight": vv["flight"],
                    "model": vv["model"],
                    "registration": vv["registration"],
                    "ladd_flag": vv["ladd_flag"],
                    "military_flag": vv["military_flag"],
                    "pia_flag": vv["pia_flag"],
                    "wierdo_flag": vv["wierdo_flag"],
                }

                vv["pg_id"] = self.postgres.adsb_exchange_select_or_insert(adsbex_args).id

            return True
        except Exception as error:
            logger.error(f"adsbex load failed: {error}")

        return False

    def load_obs(self) -> bool:
        if self.load_log_id is None or self.load_log_id < 1:
            logger.error("load_log_id is not set")
            return False
        
        try:
            adsbex = self.jh.raw_json["adsbex"]

            obs = self.jh.raw_json["observations"]
            for observation in obs:
                adsb_hex = observation["hex"]
                if adsb_hex in adsbex:
                    pg_id = adsbex[adsb_hex]["pg_id"]
                else:
                    pg_id = 1

                obs_args = {
                    "adsb_exchange_id": pg_id,
                    "adsb_hex": adsb_hex,
                    "altitude": observation["altitude"],
                    "bearing": 0,
                    "flight": observation["flight"] if len(observation["flight"]) > 0 else "unknown",
                    "latitude": observation["latitude"],
                    "longitude": observation["longitude"],
                    "load_log_id": self.load_log_id,
                    "obs_time": datetime.datetime.fromisoformat(self.jh.raw_json["timeStamp"]["iso8601"]),
                    "range": 0,
                    "speed": observation["speed"],
                    "track": observation["track"],
                }

                self.postgres.observation_insert(obs_args)

            return True
        except Exception as error:
            logger.error(f"obs load failed: {error}")

        return False

    def file_processor(self, file_name) -> None:
        if os.path.isfile(file_name) is False:
            logger.warning(f"skipping non-file:{file_name}")
            self.file_failure(file_name)
            return

        if os.path.getsize(file_name) < 1:
            logger.warning(f"skipping empty file:{file_name}")
            self.file_failure(file_name)
            return

        if not file_name.endswith(".json"):
            logger.warning(f"skipping non-json:{file_name}")
            self.file_failure(file_name)
            return

        if not self.jh.json_file_reader(file_name, True):
            logger.warning(f"json file read/verify failure for {file_name}")
            self.file_failure(file_name)
            return

        if self.jh.raw_json["fileName"] != file_name:
            logger.warning(
                f"mismatched file name: {self.jh.raw_json['fileName']} vs {file_name}"
            )
            self.file_failure(file_name)
            return

        if (
            self.jh.raw_json["version"] == 1
            and self.jh.raw_json["job"]["project"] == "hyena-v2"
        ):
            pass
        else:
            logger.warning(f"invalid version or project for {file_name}")
            self.file_failure(file_name)
            return

        if self.load_log_test(file_name):
            pass
        else:
            self.file_failure(file_name)
            return

        if self.load_adsbex():
            pass
        else:
            self.file_failure(file_name)
            return

        if self.load_obs():
            self.file_success(file_name)
        else:
            self.file_failure(file_name)

    def execute(self) -> None:
        logger.info(f"loader fresh dir:{self.fresh_dir}")

        os.chdir(self.fresh_dir)
        targets = sorted(os.listdir("."))
        logger.info(f"{len(targets)} files noted")

        for target in targets:
            self.file_processor(target)

        logger.info(f"loader success:{self.success} failure:{self.failure}")


# ;;; Local Variables: ***
# ;;; mode:python ***
# ;;; End: ***
