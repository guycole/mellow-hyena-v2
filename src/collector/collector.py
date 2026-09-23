#
# Title: collector.py
# Description: perform adsb or uat collection
# Development Environment: Ubuntu 22.04.5 LTS/python 3.10.12
# Author: G.S. Cole (guycole at gmail dot com)
#

import datetime
import json
import logging
import os
import sys
import time
import uuid
import zoneinfo

from typing import Any

import pydantic
import requests
import yaml
from yaml.loader import SafeLoader

from adsb_exchange import AdsbExchange

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("hyena")


class AdsbEx(pydantic.BaseModel):
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
    hostName: str
    hostType: str


class GeoLoc(pydantic.BaseModel):
    altitude: float
    latitude: float
    longitude: float
    siteName: str

class Job(pydantic.BaseModel):
    mode: str
    project: str
    task: str


class Observation(pydantic.BaseModel):
    hex: str
    flight: str
    latitude: str
    longitude: str
    altitude: str
    track: str
    speed: str

class Receiver(pydantic.BaseModel):
    antenna: str
    receiverId: int
    task: str
    type: str


class TimeStamp(pydantic.BaseModel):
    epochSeconds: int = pydantic.Field(default_factory=lambda: int(time.time()))
    iso8601: str = ""

    @pydantic.model_validator(mode="after")
    def sync_iso8601_from_epoch(self) -> "TimeStamp":
        self.iso8601 = datetime.datetime.fromtimestamp(
            self.epochSeconds, tz=zoneinfo.ZoneInfo("UTC")
        ).isoformat()
        return self


class HyenaModel(pydantic.BaseModel):
    crateName: str
    fileName: str
    version: int = 1
    equipment: Equipment
    geoLoc: GeoLoc
    job: Job
    receiver: Receiver
    timeStamp: TimeStamp
    adsbex: dict[str, AdsbEx]
    observations: list[Observation]


class Collector:
    """make the observation file"""

    def __init__(self, args: dict[str, Any]):
        if "dump1090" in args["receiver"]["task"]:
            self.dump1090url = args["dump1090Url"]

        if "dump978" in args["receiver"]["task"]:
            self.dump978filename = args["dump978Filename"]

        self.crate_name = args["crateName"]
        self.fresh_dir = args["freshDir"]

        self.host_name = args["equipment"]["hostName"]
        self.host_type = args["equipment"]["hostType"]

        self.altitude = args["geoLoc"]["altitude"]
        self.latitude = args["geoLoc"]["latitude"]
        self.longitude = args["geoLoc"]["longitude"]
        self.site_name = args["geoLoc"]["siteName"]

        self.antenna = args["receiver"]["antenna"]
        self.receiver_id = args["receiver"]["receiverId"]
        self.receiver_task = args["receiver"]["task"]
        self.receiver_type = args["receiver"]["type"]

        self.equipment = Equipment(**args["equipment"])
        self.geo_loc = GeoLoc(**args["geoLoc"])
        self.receiver = Receiver(**args["receiver"])
        self.time_stamp = TimeStamp()

        # hyena-v2-dump1090
        task = args["receiver"]["task"]
        tokens = task.split("-")
        mode = tokens[-1]
        project = "-".join(tokens[:-1])
        self.job = Job(mode=mode, project=project, task=task)

    @staticmethod
    def _to_text(value: Any, fallback: str) -> str:
        if value is None:
            return fallback
        return str(value).strip() or fallback

    def dump978(self) -> list[dict[str, Any]]:
        if not os.path.exists(self.dump978filename):
            logger.warning("dump978 file does not exist: %s", self.dump978filename)
            return []

        try:
            with open(self.dump978filename, "r", encoding="utf-8") as infile:
                buffer = json.load(infile)
        except OSError:
            logger.exception("dump978 file open error: %s", self.dump978filename)
            return []
        except json.JSONDecodeError:
            logger.exception("dump978 file read error: %s", self.dump978filename)
            return []

        if not isinstance(buffer, dict):
            logger.warning("dump978 payload is not an object: %s", self.dump978filename)
            return []

        raw = buffer.get("aircraft")
        if not isinstance(raw, list):
            logger.warning("dump978 missing aircraft list: %s", self.dump978filename)
            return []

        if not raw:
            logger.info("empty dump978 aircraft list: %s", self.dump978filename)
            return []

        results = []
        for element in raw:
            #   {"hex":"a6128d","lat":38.054087,"lon":-122.454450,"seen_pos":54,"altitude":4400,"vert_rate":192,"track":322,"speed":99,"messages":4,"seen":54,"rssi":0}

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

    def dump1090(self) -> list[dict[str, Any]]:
        raw = []

        try:
            response = requests.get(self.dump1090url, timeout=5.0)
            if response.status_code == 200:
                candidate = response.json()
                if isinstance(candidate, list):
                    raw = candidate
                else:
                    logger.warning("dump1090 payload is not a list")
            else:
                logger.warning("dump1090 bad response: %s", response.status_code)
        except requests.RequestException:
            logger.exception("dump1090 request failure: %s", self.dump1090url)
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

    def execute(self, adsbex_key: str | None) -> None:
        logger.info("collector execute: %s", self.receiver_task)

        os.makedirs(self.fresh_dir, exist_ok=True)
        base_file_name = str(uuid.uuid4())
        logger.info("base filename: %s", base_file_name)
        output_file_name = f"{base_file_name}.json"
        output_path = os.path.join(self.fresh_dir, output_file_name)

        if "dump1090" in self.receiver_task:
            observations = self.dump1090()
        elif "dump978" in self.receiver_task:
            observations = self.dump978()
        else:
            logger.error("unknown collection mode: %s", self.receiver_task)
            return

        candidates = [
            observation["hex"]
            for observation in observations
            if observation.get("hex") and observation["hex"] != "unknown"
        ]

        adsbex: dict[str, dict[str, Any]] = {}
        if adsbex_key:
            adsb_exchange = AdsbExchange(adsbex_key)
            adsbex = adsb_exchange.execute(candidates)
        else:
            logger.warning("skipping ADS-B Exchange lookup because no API key is available")

        hyena_model = HyenaModel(
            crateName=self.crate_name,
            fileName=output_file_name,
            equipment=self.equipment,
            geoLoc=self.geo_loc,
            job=self.job,
            receiver=self.receiver,
            timeStamp=self.time_stamp,
            adsbex=adsbex,
            observations=observations,
        )

        with open(output_path, "w", encoding="utf-8") as out_file:
            out_file.write(hyena_model.model_dump_json(indent=4))
            out_file.write("\n")

        logger.info("wrote %s observations to %s", len(observations), output_path)

#
# argv[1] = configuration filename
#
if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_name = sys.argv[1]
    else:
        file_name = "config.yaml"

    adsbex_key = None
#    with open("adsbex.key", "r") as key_file:
#        try:
#            adsbex_key = key_file.read().strip()
#        except Exception as error:
#            logger.exception("adsbex key read error: %s", error)
#            adsbex_key = None

    with open(file_name, "r", encoding="utf-8") as in_file:
        try:
            configuration = yaml.load(in_file, Loader=SafeLoader)
            collector = Collector(configuration)
            collector.execute(adsbex_key)
        except yaml.YAMLError as error:
            logger.exception("configuration parse error: %s", error)

# ;;; Local Variables: ***
# ;;; mode:python ***
# ;;; End: ***
