#
# Title: loader.py
# Description: load heeler files
# Development Environment: Ubuntu 22.04.5 LTS/python 3.10.12
# Author: G.S. Cole (guycole at gmail dot com)
#
import datetime
import logging
import os
from abc import ABC, abstractmethod

from sqlalchemy.exc import SQLAlchemyError

from helper.json_helper import JsonHelper
from helper.postgres import PostGres

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("loader")


class LoaderBase(ABC):
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


class Loader(LoaderBase):

    def __init__(self, app_logger: logging.Logger, postgres: PostGres):
        self.logger = app_logger
        self.postgres = postgres

        self.failure_dir = os.environ.get("FAILURE_DIR", "/var/peccary/hyena/failure")
        self.fresh_dir = os.environ.get("FRESH_DIR", "/var/peccary/hyena/hyena-v2")

        self.failure = 0
        self.success = 0
        self.load_log_id: int | None = None
        self.adsb_flag = True

        self.json_helper = JsonHelper(self.logger)

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

    def file_success(self, file_name: str) -> None:
        self.logger.info("file success:%s", file_name)

        self.success += 1
        try:
            os.remove(file_name)
        except OSError as error:
            self.logger.error("file delete failure for %s: %s", file_name, error)

    def load_log_test(self, test_file_name: str) -> bool:
        self.logger.info("load_log_test for file: %s", test_file_name)

        try:
            candidate = self.postgres.load_log_select_by_file_name(test_file_name)
            if candidate is None:
                self.logger.info("processing new file:%s", test_file_name)

                raw_buffer = self.json_helper.raw_json
                if not isinstance(raw_buffer, dict):
                    self.logger.warning("raw buffer missing for file: %s", test_file_name)
                    return False

                site_name = raw_buffer["geoLoc"]["siteName"]
                geo_loc = self.postgres.geo_loc_select_by_site(site_name)
                if len(geo_loc) == 0:
                    self.logger.warning(
                        "must insert geo_loc for site: %s",
                        site_name,
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
                    "site_name": site_name,
                    "source_file_name": raw_buffer.get(
                        "sourceFileName", raw_buffer.get("fileName", test_file_name)
                    ),
                    "task": raw_buffer["job"]["task"],
                }

                self.load_log_id = self.postgres.load_log_insert(load_log).id

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
                    return False

                return True
            self.logger.info("skipping already processed:%s", test_file_name)
        except (KeyError, IndexError, TypeError, ValueError) as error:
            self.logger.error("payload parsing failed for %s: %s", test_file_name, error)
        except SQLAlchemyError as error:
            self.logger.error("postgres insert failed for %s: %s", test_file_name, error)
        
        return False

    def load_adsbex(self) -> bool:
        try:
            raw_buffer = self.json_helper.raw_json
            if not isinstance(raw_buffer, dict):
                return False

            adsbex = raw_buffer["adsbex"]
            for vv in adsbex.values():
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
        except (KeyError, TypeError, SQLAlchemyError) as error:
            self.logger.error("adsbex load failed: %s", error)

        return False

    def load_obs(self) -> bool:
        if self.load_log_id is None or self.load_log_id < 1:
            self.logger.error("load_log_id is not set")
            return False

        try:
            raw_buffer = self.json_helper.raw_json
            if not isinstance(raw_buffer, dict):
                return False

            adsbex = raw_buffer["adsbex"]

            obs = raw_buffer["observations"]
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
                    "obs_time": datetime.datetime.fromisoformat(
                        raw_buffer["timeStamp"]["iso8601"]
                    ),
                    "range": 0,
                    "speed": observation["speed"],
                    "track": observation["track"],
                }

                self.postgres.observation_insert(obs_args)

            return True
        except (KeyError, TypeError, ValueError, SQLAlchemyError) as error:
            self.logger.error("obs load failed: %s", error)

        return False

    def file_processor(self, file_name: str) -> bool:
        self.logger.info("processing file:%s", file_name)

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
            self.logger.warning("json file read/verify failure for %s", file_name)
            self.file_failure(file_name)
            return False

        raw_buffer = self.json_helper.raw_json
        if not isinstance(raw_buffer, dict):
            self.file_failure(file_name)
            return False

        if raw_buffer["fileName"] != file_name:
            self.logger.warning(
                "mismatched file name: %s vs %s", raw_buffer["fileName"], file_name
            )
            self.file_failure(file_name)
            return False

        if (
            raw_buffer["version"] == 1
            and raw_buffer["job"]["project"] == "hyena-v2"
        ):
            pass
        else:
            self.logger.warning("invalid version or project for %s", file_name)
            self.file_failure(file_name)
            return False

        if not self.load_log_test(file_name):
            self.file_failure(file_name)
            return False

        if not self.load_adsbex():
            self.file_failure(file_name)
            return False

        if self.load_obs():
            self.file_success(file_name)
            return True

        self.file_failure(file_name)
        return False

    def execute(self) -> int:
        self.logger.info("loader fresh dir:%s", self.fresh_dir)

        if not os.path.isdir(self.fresh_dir):
            self.logger.error("fresh dir missing:%s", self.fresh_dir)
            return 1

        os.chdir(self.fresh_dir)
        targets = sorted(os.listdir("."))
        self.logger.info("%s files noted", len(targets))

        for target in targets:
            self.file_processor(target)

        self.logger.info("loader success:%s failure:%s", self.success, self.failure)
        return 0


def _run_as_script() -> int:
    logger.error("Run via hyena_app.py with stuntbox=loader")
    return 1


if __name__ == "__main__":
    raise SystemExit(_run_as_script())


# ;;; Local Variables: ***
# ;;; mode:python ***
# ;;; End: ***
