#
# Title: validator.py
# Description: ensure valid hyena files
# Development Environment: Ubuntu 22.04.5 LTS/python 3.10.12
# Author: G.S. Cole (guycole at gmail dot com)
#
import datetime
import logging
import os
from abc import ABC, abstractmethod

from helper.json_helper import JsonHelper
from helper.postgres import PostGres
from sqlalchemy.exc import SQLAlchemyError

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("validator")


class Validator(ABC):

    @abstractmethod
    def file_processor(self, file_name: str) -> bool:
        pass

    @abstractmethod
    def execute(self) -> int:
        pass

    @abstractmethod
    def file_failure(self, file_name: str) -> None:
        pass

    @abstractmethod
    def file_success(self, file_name: str) -> None:
        pass

    @abstractmethod
    def load_log_test(self, test_file_name: str) -> bool:
        pass


class HyenaValidator(Validator):
    def __init__(self, app_logger: logging.Logger, postgres: PostGres):
        self.logger = app_logger
        self.postgres = postgres

        self.failure_dir = os.environ.get("FAILURE_DIR", "/var/wombat/failure")
        self.fresh_dir = os.environ.get("FRESH_DIR", "/var/wombat/fresh/hyena")
        self.success_dir_adsb = os.environ.get(
            "SUCCESS_DIR_ADSB", "/var/wombat/hyena/success_adsb"
        )
        self.success_dir_uat = os.environ.get(
            "SUCCESS_DIR_UAT", "/var/wombat/hyena/success_uat"
        )

        self.failure = 0
        self.skipped = 0
        self.success_adsb = 0
        self.success_uat = 0

        self.adsb_flag = True
        self.skip_current_file = False

        self.json_helper = JsonHelper()

    def file_failure(self, file_name: str) -> None:
        self.logger.info("file failure:%s", file_name)

        self.failure += 1
        failure_target = os.path.join(self.failure_dir, file_name)
        try:
            os.rename(file_name, failure_target)
        except OSError as error:
            self.logger.error(
                "file move failure for %s -> %s: %s", file_name, failure_target, error
            )

    def _success_target(self, file_name: str) -> str:
        if self.adsb_flag:
            return os.path.join(self.success_dir_adsb, file_name)

        return os.path.join(self.success_dir_uat, file_name)

    def file_success(self, file_name: str) -> None:
        self.logger.info("file success:%s", file_name)

        if self.adsb_flag:
            self.success_adsb += 1
        else:
            self.success_uat += 1

        success_target = self._success_target(file_name)
        try:
            os.rename(file_name, success_target)
        except OSError as error:
            self.logger.error(
                "file move failure for %s -> %s: %s", file_name, success_target, error
            )

    def load_log_test(self, test_file_name: str) -> bool:
        self.logger.info("load_log_test for file: %s", test_file_name)
        self.skip_current_file = False

        try:
            candidate = self.postgres.load_log_select_by_file_name(test_file_name)
            if candidate is not None:
                self.logger.info("skipping already processed:%s", test_file_name)
                self.skip_current_file = True
                return False

            self.logger.info("processing new file:%s", test_file_name)

            raw_buffer = self.json_helper.raw_json
            if not isinstance(raw_buffer, dict):
                self.logger.warning("raw buffer missing for file: %s", test_file_name)
                return False

            geo_loc = self.postgres.geo_loc_select_by_site(raw_buffer["geoLoc"]["siteName"])
            if len(geo_loc) == 0:
                self.logger.warning(
                    "must insert geo_loc for site: %s", raw_buffer["geoLoc"]["siteName"]
                )
                return False

            load_log = {
                "adsbex_quantity": len(raw_buffer["adsbex"]),
                "crate_name": raw_buffer["crateName"],
                "epoch_seconds": raw_buffer["timeStamp"]["epochSeconds"],
                "file_name": test_file_name,
                "geo_loc_id": geo_loc[0].id,
                "host_name": raw_buffer["equipment"]["hostName"],
                "load_time": datetime.datetime.now(datetime.timezone.utc),
                "mode": raw_buffer["job"]["mode"],
                "obs_quantity": len(raw_buffer["observations"]),
                "obs_time": raw_buffer["timeStamp"]["iso8601"],
                "site_name": raw_buffer["geoLoc"]["siteName"],
                "task": raw_buffer["job"]["task"],
            }

            self.postgres.load_log_insert(load_log)

            if raw_buffer["job"]["mode"] == "dump1090":
                self.adsb_flag = True
                quantity_adsb = len(raw_buffer["observations"])
                quantity_uat = 0
            else:
                self.adsb_flag = False
                quantity_adsb = 0
                quantity_uat = len(raw_buffer["observations"])

            daily_score = {
                "crate_name": raw_buffer["crateName"],
                "file_quantity": 1,
                "host_name": raw_buffer["equipment"]["hostName"],
                "quantity_adsb": quantity_adsb,
                "quantity_uat": quantity_uat,
                "score_date": datetime.date.fromisoformat(
                    raw_buffer["timeStamp"]["iso8601"][:10]
                ),
            }

            self.postgres.daily_score_insert_or_update(daily_score)

            if len(raw_buffer["observations"]) < 1:
                self.logger.info("skipping file with no observations")
                self.skip_current_file = True
                return False

            return True
        except (KeyError, IndexError, TypeError, ValueError) as error:
            self.logger.error("payload parsing failed for %s: %s", test_file_name, error)
        except SQLAlchemyError as error:
            self.logger.error("postgres insert failed for %s: %s", test_file_name, error)

        return False

    def file_processor(self, file_name: str) -> bool:
        self.logger.info("processing file: %s", file_name)

        if not os.path.isfile(file_name):
            self.logger.warning("skipping non-file:%s", file_name)
            self.file_failure(file_name)
            return False

        if os.path.getsize(file_name) < 1:
            self.logger.warning("skipping empty file:%s", file_name)
            self.file_failure(file_name)
            return False

        if not file_name.endswith(".json"):
            self.logger.warning("skipping non-json:%s", file_name)
            self.file_failure(file_name)
            return False

        if not self.json_helper.json_file_reader(file_name, True):
            self.logger.warning("file read failed for %s", file_name)
            self.file_failure(file_name)
            return False

        raw_buffer = self.json_helper.raw_json
        if not isinstance(raw_buffer, dict):
            self.logger.warning("invalid raw payload for %s", file_name)
            self.file_failure(file_name)
            return False

        version = raw_buffer.get("version")
        project = raw_buffer.get("job", {}).get("project")
        if version != 1 or project != "hyena-v2":
            self.logger.warning("invalid version or project for %s", file_name)
            self.file_failure(file_name)
            return False

        if self.load_log_test(file_name):
            self.file_success(file_name)
            return True

        if self.skip_current_file:
            self.skipped += 1
            self.logger.info("file skipped:%s", file_name)
            return False

        self.file_failure(file_name)
        return False

    def execute(self) -> int:
        self.logger.info("validator fresh dir:%s", self.fresh_dir)
        if not os.path.isdir(self.fresh_dir):
            self.logger.error("fresh dir missing:%s", self.fresh_dir)
            return 1

        os.chdir(self.fresh_dir)
        targets = sorted(os.listdir("."))
        self.logger.info("%s files noted", len(targets))

        for target in targets:
            self.file_processor(target)

        self.logger.info(
            "validator adsb success:%s uat success:%s skipped:%s failure:%s",
            self.success_adsb,
            self.success_uat,
            self.skipped,
            self.failure,
        )

        return 0


if __name__ == "__main__":
    logger.error("Run via hyena_app.py with stuntbox=validator")
    raise SystemExit(1)

# ;;; Local Variables: ***
# ;;; mode:python ***
# ;;; End: ***
