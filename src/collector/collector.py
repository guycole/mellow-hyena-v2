#
# Title: collector.py
# Description: 
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
import uuid
import zoneinfo

import yaml
from yaml.loader import SafeLoader

from adsb_exchange import AdsbExchange

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("hyena-adsb")

class Collector:
    """make the observation file"""

    def __init__(self, args: dict[str, any]):
        if "dump1090" in args["receiver"]["task"]:
            self.dump1090url = args["dump1090Url"]

        if "dump978" in args["receiver"]["task"]:
            self.dump978filename = args["dump978Filename"]

        self.crate_name = args["crateName"]
        self.fresh_dir = args["freshDir"]

        self.host_name = args['host']["name"]
        self.host_type = args['host']["type"]

        self.altitude = args["geoLoc"]["altitude"]
        self.latitude = args["geoLoc"]["latitude"]
        self.longitude = args["geoLoc"]["longitude"]
        self.site_name = args["geoLoc"]["siteName"]

        self.antenna = args["receiver"]["antenna"]
        self.receiver_id = args["receiver"]["receiver_id"]
        self.receiver_task = args["receiver"]["task"]
        self.receiver_type = args["receiver"]["type"]

    def dump978(self) -> list[dict[str, any]]:
        buffer = {}

        with open(self.dump978filename, "r", encoding="utf-8") as infile:
            try:
                buffer = json.load(infile)
                if len(buffer) < 1:
                    print(f"empty file noted: {self.dump978filename}")
                    return []
            except:
                print(f"file read error: {self.dump978filename}")

        results = []    
        raw = buffer.get("aircraft", [])
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
    
    def dump1090(self) -> list[dict[str, any]]:
        raw = []

        try:
            response = requests.get(self.dump1090url, timeout=5.0)
            if response.status_code == 200:
                raw = json.loads(response.text)
        except Exception as error:
            print(f"dump1090 error: {error}")

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
    
    def json_file_writer(self, file_name: str, json_data: dict[str, any]) -> None:
        try:
            with open(file_name, "w") as out_file:
                json.dump(json_data, out_file, indent=4)
        except Exception as error:
            print(error)

    def execute(self, adsbex_key:str) -> None:
        print(f"collector execute: {self.receiver_task}")

        base_file_name = str(uuid.uuid4())
        print(f"base filename: {base_file_name}")

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
            print(f"unknown receiver task: {self.receiver_task}")

        candidates = [observation["hex"] for observation in observations]

        adsb_exchange = AdsbExchange(adsbex_key)
        adsbex = adsb_exchange.execute(candidates)

        results = {
            "equipment": {
                "antenna": self.antenna,  
                "receiver_id": self.receiver_id,
                "receiver_type": self.receiver_type,
                "platform": self.host_type,
                "hostName": self.host_name  
            },
            "geoLoc": {
                "altitude": self.altitude,
                "latitude": self.latitude,
                "longitude": self.longitude,
                "siteName": self.site_name
            },
            "timeStamp": {
                "epochSeconds": epoch_seconds,
                "iso8601": dt_object_utc.isoformat()
            },
            "crate": self.crate_name,
            "fileName": f"{base_file_name}.json",
            "mode": mode,
            "project": self.receiver_task,
            "version": 1,
            "adsbex": adsbex,
            "observations": observations
        }

        self.json_file_writer(outfile_json, results)

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
            print(error)
            adsbex_key = None

    with open(file_name, "r") as in_file:
        try:
            configuration = yaml.load(in_file, Loader=SafeLoader)
            collector = Collector(configuration)
            collector.execute(adsbex_key)
        except yaml.YAMLError as error:
            print(error)

# ;;; Local Variables: ***
# ;;; mode:python ***
# ;;; End: ***
