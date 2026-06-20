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
        self.dump1090url = args["dump1090url"]
        self.dump978filename = args["dump978filename"]

        self.crate_name = args["crateName"]
        self.fresh_dir = configuration["freshDir"]

        self.host_name = configuration['equipment']["hostName"]
        self.host_type = configuration['equipment']["type"]

        self.altitude = configuration["geoLoc"]["altitude"]
        self.latitude = configuration["geoLoc"]["latitude"]
        self.longitude = configuration["geoLoc"]["longitude"]
        self.site_name = configuration["geoLoc"]["siteName"]

        self.antenna = configuration["receiver"]["antenna"]
        self.receiver_id = configuration["receiver"]["receiver_id"]
        self.receiver_task = configuration["receiver"]["task"]
        self.receiver_type = configuration["receiver"]["type"]

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

    def dump978(self) -> list[dict[str, any]]:
        dump978out = "/tmp/aircraft.json"

        raw = []
        return []

    def execute2(self, stunt) -> None:
        print(f"collector execute:{stunt}")

        base_file_name = str(uuid.uuid4())
        print(f"base filename: {base_file_name}")

        epoch_seconds = int(time.time())
        dt_object_utc = datetime.datetime.fromtimestamp(
            epoch_seconds, tz=zoneinfo.ZoneInfo("UTC")
        )

        outfile_json = f"{self.fresh_dir}/{base_file_name}.json"

        if stunt == "adsb":
            observations = self.dump1090()
        elif stunt == "uat":
            observations = self.dump978()
        else:
            print(f"unkown stunt")

        observations = self.dump1090()
        candidates = [observation["hex"] for observation in observations]
        print(candidates)

        adsb_exchange = AdsbExchange("bogus")
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
            "mode": "dump1090",
            "project": "hyena-adsb-v2",
            "version": 1,
            "adsbex": adsbex,
            "observations": observations
        }

        self.json_file_writer(outfile_json, results)

    def execute(self) -> None:
        print(f"collector execute")

        if "uat" in self.receiver_task:
            print("UAT receiver task detected.")
        else:
            print("adsb")

#
# argv[1] = configuration filename
#
if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_name = sys.argv[1]
    else:
        file_name = "config.yaml"

    with open(file_name, "r") as in_file:
        try:
            configuration = yaml.load(in_file, Loader=SafeLoader)
            collector = Collector(configuration)
            collector.execute()
        except yaml.YAMLError as error:
            print(error)

# ;;; Local Variables: ***
# ;;; mode:python ***
# ;;; End: ***
