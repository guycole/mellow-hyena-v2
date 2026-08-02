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

from helper.json_helper import JsonHelper, schema

from helper.postgres import PostGres

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("loader")


class Loader:

    def __init__(self, postgres: PostGres):
        self.postgres = postgres

        self.failure_dir = os.environ.get("FAILURE_DIR", "/var/peccary/heeler/failure")
        self.fresh_dir = os.environ.get("FRESH_DIR", "/var/peccary/heeler/heeler-v2")

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

    def load_log(self, file_name: str) -> bool:
        try:
            candidate = self.postgres.load_log_select_by_file_name(file_name)
            if candidate is not None:
                logger.info(f"skippping already processed:{file_name}")
                return False
            else:
                geo_loc = self.postgres.geo_loc_select_by_site(
                    self.jh.raw_json["geoLoc"]["siteName"]
                )
                if len(geo_loc) == 0:
                    logger.error(
                        f"must insert geo_loc for site: {self.jh.raw_json['geoLoc']['siteName']}"
                    )
                    return False

                # todo handle mobile or missing geoloc
                geo_loc_id = geo_loc[0].id

                candidate = {
                    "crate_name": self.jh.raw_json["crateName"],
                    "epoch_seconds": self.jh.raw_json["timeStamp"]["epochSeconds"],
                    "file_name": file_name,
                    "geo_loc_id": geo_loc_id,
                    "host_name": self.jh.raw_json["equipment"]["hostName"],
                    "load_time": datetime.datetime.now(),
                    "mode": self.jh.raw_json["job"]["mode"],
                    "obs_quantity": len(self.jh.raw_json["observations"]),
                    "obs_time": self.jh.raw_json["timeStamp"]["iso8601"],
                    "site_name": self.jh.raw_json["geoLoc"]["siteName"],
                    "task": self.jh.raw_json["job"]["task"],
                }

                self.load_log_id = self.postgres.load_log_insert(candidate).id

                daily_score = {
                    "crate_name": self.jh.raw_json["crateName"],
                    "file_quantity": 1,
                    "host_name": self.jh.raw_json["equipment"]["hostName"],
                    "obs_quantity": len(self.jh.raw_json["observations"]),
                    "score_date": datetime.date.fromisoformat(
                        self.jh.raw_json["timeStamp"]["iso8601"][:10]
                    ),
                }

                self.postgres.daily_score_insert_or_update(daily_score)

                return True
        except Exception as error:
            logger.error(f"postgres insert failed for {file_name}: {error}")

        return False

    def load_obs(self) -> None:
        try:
            observations = self.jh.raw_json["observations"]
            for obs in observations:
                wap_id = self.postgres.wap_select(self.make_wap_from_obs(obs, 1))[0].id

                candidate = {
                    "bssid": obs["bssid"],
                    "load_log_id": self.load_log_id,
                    "obs_time": self.jh.raw_json["timeStamp"]["iso8601"],
                    "signal_dbm": obs["signal_dbm"],
                    "wap_id": wap_id,
                }

                self.postgres.observation_insert(candidate)
        except Exception as error:
            logger.error(f"failed to load observations: {error}")

    def make_wap_from_obs(self, obs: dict[str, any], version: int) -> dict[str, any]:
        bssid = obs["bssid"].lower()
        return {
            "bssid": bssid.strip(),
            "capability": obs["capabilities"].strip(),
            "cipher": (obs.get("cipher_type") or "xstubx").strip(),
            "frequency_mhz": obs["frequency_mhz"],
            "key": f"{bssid}_{version}",
            "ssid": (obs.get("ssid") or "xstubx").strip(),
            "version": version,
        }

    def match_wap(self, wap1: dict[str, any], wap2: dict[str, any]) -> bool:
        return (
            wap1["frequency_mhz"] == wap2["frequency_mhz"]
            and wap1["ssid"] == wap2["ssid"]
            and wap1["capability"] == wap2["capability"]
            and wap1["cipher"] == wap2["cipher"]
        )

    def load_wap(self) -> None:
        # consolidate WAPs from observations, versioning by bssid when attributes differ
        candidates = {}

        for observation in self.jh.raw_json["observations"]:
            bssid = observation["bssid"].lower()

            # gather all existing entries for this bssid
            existing = {k: v for k, v in candidates.items() if v["bssid"] == bssid}

            if not existing:
                # first occurrence of this bssid
                temp = self.make_wap_from_obs(observation, 1)
                candidates[temp["key"]] = temp
            else:
                # check if any existing version already matches this observation
                probe = self.make_wap_from_obs(observation, 0)
                if any(self.match_wap(v, probe) for v in existing.values()):
                    pass  # exact duplicate, skip
                else:
                    # distinct wap for this bssid: assign next version
                    next_version = max(v["version"] for v in existing.values()) + 1
                    temp = self.make_wap_from_obs(observation, next_version)
                    candidates[temp["key"]] = temp
                    logger.info(f"new wap version {next_version} for bssid {bssid}")

        logger.info(
            f"load_wap: {len(candidates)} unique WAPs from {len(self.jh.raw_json['observations'])} observations"
        )

        for candidate in candidates.values():
            try:
                selected_wap = self.postgres.wap_select(candidate)
                if len(selected_wap) < 1:
                    # no exact match in DB — find the max version already stored for this bssid
                    db_versions = self.postgres.wap_select_by_bssid(candidate["bssid"])
                    if db_versions:
                        candidate["version"] = max(w.version for w in db_versions) + 1
                        candidate["key"] = (
                            f"{candidate['bssid']}_{candidate['version']}"
                        )
                    self.postgres.wap_insert(candidate)
            except Exception as error:
                logger.error(f"failed to load wap: {error}")

    def file_processor(self, file_name) -> None:
        if os.path.isfile(file_name) is False:
            logger.warning(f"skipping non-file:{file_name}")
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
            and self.jh.raw_json["job"]["project"] == "heeler-v2"
        ):
            pass
        else:
            logger.warning(f"invalid version or project for {file_name}")
            self.file_failure(file_name)
            return

        if self.load_log(file_name):
            self.load_wap()
            self.load_obs()
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

        logger.info(f"validator success:{self.success} failure:{self.failure}")


# ;;; Local Variables: ***
# ;;; mode:python ***
# ;;; End: ***
