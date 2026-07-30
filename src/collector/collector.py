#
# Title: collector.py
# Description: perform adsb or uat collection
# Development Environment: Ubuntu 22.04.5 LTS/python 3.10.12
# Author: G.S. Cole (guycole at gmail dot com)
#

import datetime
import json
import logging
import requests
import socket
import sys
import time
from typing import Any
import uuid
import zoneinfo

from helper.json_helper import JsonHelper

import yaml
from yaml.loader import SafeLoader

from adsb_exchange import AdsbExchange

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("hyena")

class Collector:
    """make the observation file"""

    def __init__(self, args: dict[str, Any]):
        if "dump1090" in args["receiver"]["task"]:
            self.dump1090url = args["dump1090Url"]

        if "dump978" in args["receiver"]["task"]:
            self.dump978filename = args["dump978Filename"]

        self.crate_name = args["crateName"]
        self.fresh_dir = args["freshDir"]

        self.host_name = args['equipment']["hostName"]
        self.host_type = args['equipment']["hostType"]

        self.altitude = args["geoLoc"]["altitude"]
        self.latitude = args["geoLoc"]["latitude"]
        self.longitude = args["geoLoc"]["longitude"]
        self.site_name = args["geoLoc"]["siteName"]

        self.antenna = args["receiver"]["antenna"]
        self.receiver_id = args["receiver"]["receiverId"]
        self.receiver_task = args["receiver"]["task"]
        self.receiver_type = args["receiver"]["type"]

    def dump978(self) -> list[dict[str, Any]]:
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
                "hex": element.get("hex", "unknown").strip(),
                "latitude": str(element.get("lat", 0.0)).strip(),
                "longitude": str(element.get("lon", 0.0)).strip(),
                "altitude": str(element.get("altitude", 0)).strip(),
                "track": str(element.get("track", 0)).strip(),
                "speed": str(element.get("speed", 0)).strip(),
            }

            results.append(temp)

        return results
    
    def dump1090(self) -> list[dict[str, Any]]:
        raw = []

        try:
            response = requests.get(self.dump1090url, timeout=5.0)
            if response.status_code == 200:
                raw = json.loads(response.text)
        except Exception as error:
            logger.error("dump1090 error: %s", error)

        results = []
        for element in raw:
            temp = {
                "hex": element.get("hex", "unknown").strip(),
                "flight": element.get("flight", "unknown").strip(),
                "latitude": str(element.get("lat", 0.0)).strip(),
                "longitude": str(element.get("lon", 0.0)).strip(),
                "altitude": str(element.get("altitude", 0)).strip(),
                "track": str(element.get("track", 0)).strip(),
                "speed": str(element.get("speed", 0)).strip()
            }

            results.append(temp)

        return results

    def execute(self, adsbex_key: str | None) -> None:
        logger.info("collector execute: %s", self.receiver_task)

        base_file_name = str(uuid.uuid4())
        logger.info("base filename: %s", base_file_name)

        epoch_seconds = int(time.time())
        dt_object_utc = datetime.datetime.fromtimestamp(
            epoch_seconds, tz=zoneinfo.ZoneInfo("UTC")
        )

        outfile_json = f"{self.fresh_dir}/{base_file_name}.json"

        if "dump1090" in self.receiver_task:
            mode = "dump1090"
            observations = self.dump1090()
        elif "dump978" in self.receiver_task:
            mode = "dump978"
            observations = self.dump978()
        else:
            logger.error("unknown collection mode: %s", self.receiver_task)
            return

        candidates = [observation["hex"] for observation in observations]

        adsbex = {}
        if adsbex_key:
            adsb_exchange = AdsbExchange(adsbex_key)
            adsbex = adsb_exchange.execute(candidates)
        else:
            logger.warning("skipping ADS-B Exchange lookup because no API key is available")

        results = {
            "equipment": {
                "antenna": self.antenna,  
                "receiverId": self.receiver_id,
                "receiverType": self.receiver_type,
                "hostName": self.host_name,  
                "hostType": self.host_type,
            },
            "geoLoc": {
                "altitude": self.altitude,
                "latitude": self.latitude,
                "longitude": self.longitude,
                "siteName": self.site_name,
            },
            "job": {
                "mode": mode,
                "project": "hyena-v2",
                "task": self.receiver_task,
            },
            "timeStamp": {
                "epochSeconds": epoch_seconds,
                "iso8601": dt_object_utc.isoformat(),
            },
            "crateName": self.crate_name,
            "fileName": f"{base_file_name}.json",
            "version": 1,
            "adsbex": adsbex,
            "observations": observations,
        }

        JsonHelper().json_file_writer(outfile_json, results)

#
# argv[1] = configuration filename
#
if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_name = sys.argv[1]
    else:
        file_name = "config.yaml"

    with open("adsbex.key", "r") as key_file:
        try:
            adsbex_key = key_file.read().strip()
        except Exception as error:
            logger.exception("adsbex key read error: %s", error)
            adsbex_key = None

    with open(file_name, "r") as in_file:
        try:
            configuration = yaml.load(in_file, Loader=SafeLoader)
            collector = Collector(configuration)
            collector.execute(adsbex_key)
        except yaml.YAMLError as error:
            logger.exception("configuration parse error: %s", error)

# ;;; Local Variables: ***
# ;;; mode:python ***
# ;;; End: ***
