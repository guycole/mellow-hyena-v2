#
# Title: collector.py
# Description: perform ADS-B or UAT collection
# Development Environment: Ubuntu 22.04.5 LTS/python 3.10.12
# Author: G.S. Cole (guycole at gmail dot com)
#

from __future__ import annotations

import datetime
import json
import logging
import os
import sys
import time
import uuid
import zoneinfo
from abc import ABC, abstractmethod
from typing import Any

import pydantic
import requests
import yaml
from yaml.loader import SafeLoader

from adsb_exchange import AdsbExchange

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("hyena")


class AdsbEx(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(populate_by_name=True)

    adsb_hex: str
    category: str
    emergency: str
    flight: str
    registration: str
    model: str
    ladd_flag: bool
    military_flag: bool
    pia_flag: bool
    wierdo_flag: bool


class Equipment(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(populate_by_name=True)

    host_name: str = pydantic.Field(alias="hostName")
    host_type: str = pydantic.Field(alias="hostType")


class GeoLoc(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(populate_by_name=True)

    altitude: float
    latitude: float
    longitude: float
    site_name: str = pydantic.Field(alias="siteName")


class Job(pydantic.BaseModel):
    mode: str
    project: str
    task: str


class Observation(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(populate_by_name=True)

    hex: str
    flight: str
    latitude: str
    longitude: str
    altitude: str
    track: str
    speed: str


class Receiver(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(populate_by_name=True)

    antenna: str
    receiver_id: int = pydantic.Field(alias="receiverId")
    task: str
    type: str


class TimeStamp(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(populate_by_name=True)

    epoch_seconds: int = pydantic.Field(
        default_factory=lambda: int(time.time()), alias="epochSeconds"
    )
    iso8601: str = ""

    @pydantic.model_validator(mode="after")
    def sync_iso8601_from_epoch(self) -> "TimeStamp":
        self.iso8601 = datetime.datetime.fromtimestamp(
            self.epoch_seconds, tz=zoneinfo.ZoneInfo("UTC")
        ).isoformat()
        return self


class HyenaModel(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(populate_by_name=True)

    crate_name: str = pydantic.Field(alias="crateName")
    file_name: str = pydantic.Field(alias="fileName")
    version: int = 1
    equipment: Equipment
    geo_loc: GeoLoc = pydantic.Field(alias="geoLoc")
    job: Job
    receiver: Receiver
    time_stamp: TimeStamp = pydantic.Field(alias="timeStamp")
    adsbex: dict[str, AdsbEx]
    observations: list[Observation]


class Collector(ABC):
    @abstractmethod
    def get_observations(self) -> list[Observation]:
        pass

    @abstractmethod
    def execute(self, adsbex_key: str | None = None) -> int:
        pass


class HyenaCollector(Collector):
    def __init__(self, args: dict[str, Any]):
        receiver_task = str(args["receiver"]["task"])

        self.dump1090_url = args.get("dump1090Url", "")
        self.dump978_filename = args.get("dump978Filename", "")

        self.crate_name = args["crateName"]
        self.fresh_dir = args["freshDir"]

        self.equipment = Equipment(**args["equipment"])
        self.geo_loc = GeoLoc(**args["geoLoc"])
        self.receiver = Receiver(**args["receiver"])
        self.time_stamp = TimeStamp()

        tokens = receiver_task.split("-")
        if len(tokens) > 1:
            mode = tokens[-1]
            project = "-".join(tokens[:-1])
        else:
            mode = "default"
            project = receiver_task

        self.job = Job(mode=mode, project=project, task=receiver_task)

    @staticmethod
    def _to_text(value: Any, fallback: str) -> str:
        if value is None:
            return fallback
        return str(value).strip() or fallback

    def _dump978(self) -> list[dict[str, Any]]:
        if not self.dump978_filename:
            logger.warning("dump978 filename is not configured")
            return []

        if not os.path.exists(self.dump978_filename):
            logger.warning("dump978 file does not exist: %s", self.dump978_filename)
            return []

        try:
            with open(self.dump978_filename, "r", encoding="utf-8") as infile:
                buffer = json.load(infile)
        except OSError:
            logger.exception("dump978 file open error: %s", self.dump978_filename)
            return []
        except json.JSONDecodeError:
            logger.exception("dump978 file read error: %s", self.dump978_filename)
            return []

        if not isinstance(buffer, dict):
            logger.warning(
                "dump978 payload is not an object: %s", self.dump978_filename
            )
            return []

        raw = buffer.get("aircraft")
        if not isinstance(raw, list):
            logger.warning("dump978 missing aircraft list: %s", self.dump978_filename)
            return []

        if not raw:
            logger.info("empty dump978 aircraft list: %s", self.dump978_filename)
            return []

        results = []
        for element in raw:
            temp = {
                "hex": self._to_text(element.get("hex"), "unknown"),
                "flight": self._to_text(element.get("flight"), "unknown"),
                "latitude": self._to_text(element.get("lat"), "0.0"),
                "longitude": self._to_text(element.get("lon"), "0.0"),
                "altitude": self._to_text(element.get("altitude"), "0"),
                "track": self._to_text(element.get("track"), "0"),
                "speed": self._to_text(element.get("speed"), "0"),
            }

            results.append(temp)

        return results

    def _dump1090(self) -> list[dict[str, Any]]:
        raw = []

        if not self.dump1090_url:
            logger.warning("dump1090 URL is not configured")
            return []

        try:
            response = requests.get(self.dump1090_url, timeout=5.0)
            if response.status_code == 200:
                candidate = response.json()
                if isinstance(candidate, list):
                    raw = candidate
                else:
                    logger.warning("dump1090 payload is not a list")
            else:
                logger.warning("dump1090 bad response: %s", response.status_code)
        except requests.RequestException:
            logger.exception("dump1090 request failure: %s", self.dump1090_url)
        except Exception as error:
            logger.error("dump1090 error: %s", error)

        results = []
        for element in raw:
            temp = {
                "hex": self._to_text(element.get("hex"), "unknown"),
                "flight": self._to_text(element.get("flight"), "unknown"),
                "latitude": self._to_text(element.get("lat"), "0.0"),
                "longitude": self._to_text(element.get("lon"), "0.0"),
                "altitude": self._to_text(element.get("altitude"), "0"),
                "track": self._to_text(element.get("track"), "0"),
                "speed": self._to_text(element.get("speed"), "0"),
            }

            results.append(temp)

        return results

    def get_observations(self) -> list[Observation]:
        receiver_task = self.receiver.task.lower()

        if "dump1090" in receiver_task:
            raw_observations = self._dump1090()
        elif "dump978" in receiver_task:
            raw_observations = self._dump978()
        else:
            logger.error("unknown collection mode: %s", self.receiver.task)
            return []

        return [Observation(**raw_observation) for raw_observation in raw_observations]

    def execute(self, adsbex_key: str | None = None) -> int:
        logger.info("collector execute: %s", self.receiver.task)

        os.makedirs(self.fresh_dir, exist_ok=True)
        base_file_name = str(uuid.uuid4())
        logger.info("base filename: %s", base_file_name)
        output_file_name = f"{base_file_name}.json"
        output_path = os.path.join(self.fresh_dir, output_file_name)

        observations = self.get_observations()

        candidates = [
            observation.hex
            for observation in observations
            if observation.hex != "unknown"
        ]

        adsbex: dict[str, dict[str, Any]] = {}
        if adsbex_key:
            adsb_exchange = AdsbExchange(adsbex_key)
            adsbex = adsb_exchange.execute(candidates)
        else:
            logger.warning(
                "skipping ADS-B Exchange lookup because no API key is available"
            )

        hyena_model = HyenaModel(
            crate_name=self.crate_name,
            file_name=output_file_name,
            equipment=self.equipment,
            geo_loc=self.geo_loc,
            job=self.job,
            receiver=self.receiver,
            time_stamp=self.time_stamp,
            adsbex=adsbex,
            observations=observations,
        )

        with open(output_path, "w", encoding="utf-8") as out_file:
            out_file.write(hyena_model.model_dump_json(indent=4, by_alias=True))
            out_file.write("\n")

        logger.info("wrote %s observations to %s", len(observations), output_path)
        return 0


#
# argv[1] = configuration filename
#
if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_name = sys.argv[1]
    else:
        file_name = "config.yaml"

    adsbex_key = None

    with open(file_name, "r", encoding="utf-8") as in_file:
        try:
            configuration = yaml.load(in_file, Loader=SafeLoader)
            collector = HyenaCollector(configuration)
            raise SystemExit(collector.execute(adsbex_key))
        except yaml.YAMLError as error:
            logger.exception("configuration parse error: %s", error)
            raise SystemExit(1)

# ;;; Local Variables: ***
# ;;; mode:python ***
# ;;; End: ***
