#
# Title: collector.py
# Description: 
# Development Environment: Ubuntu 22.04.5 LTS/python 3.10.12
# Author: G.S. Cole (guycole at gmail dot com)
#

import datetime
import json
import requests
import socket
import sys
import time
import uuid
import zoneinfo

import yaml
from yaml.loader import SafeLoader

class Collector:
    """make the iwlist observation file"""

    def __init__(self, args: dict[str, any]):
        self.dump1090url = args["dump1090url"]

        self.fresh_dir = args["freshDir"]

        self.altitude = args["altitude"]
        self.latitude = args["latitude"]
        self.longitude = args["longitude"]
        self.site = args["site"]

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
                "hex": element.get("hex", "unknown"),
                "flight": element.get("flight", "unknown"),
                "latitude": element.get("lat", 0.0),
                "longitude": element.get("lon", 0.0),
                "altitude": element.get("altitude", 0),
                "track": element.get("track", 0),
                "speed": element.get("speed", 0)
            }

            results.append(temp)

        return results
    
    def json_file_writer(self, file_name: str, json_data: dict[str, any]) -> None:
        try:
            with open(file_name, "w") as out_file:
                json.dump(json_data, out_file, indent=4)
        except Exception as error:
            print(error)

    def execute(self) -> None:
        print(f"collector execute")

        base_file_name = str(uuid.uuid4())
        print(f"base filename: {base_file_name}")

        outfile_json = f"{self.fresh_dir}/{base_file_name}.json"

        observations = self.dump1090()

        epoch_seconds = int(time.time())
        dt_object_utc = datetime.datetime.fromtimestamp(
            epoch_seconds, tz=zoneinfo.ZoneInfo("UTC")
        )

        results = {
            "geoLoc": {
                "altitude": self.altitude,
                "latitude": self.latitude,
                "longitude": self.longitude,
                "site": self.site
            },
            "epochSeconds": epoch_seconds, 
            "fileName": f"{base_file_name}.json",
            "iso8601": dt_object_utc.isoformat(),
            "mode": "dump1090",
            "platform": socket.gethostname(),
            "project": "hyena-v2",
            "version": 1,
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
