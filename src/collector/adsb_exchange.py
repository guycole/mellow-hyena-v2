"""adsb exchange API wrapper"""

import logging
from urllib import response
import requests
import sys

import yaml
from yaml.loader import SafeLoader

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("hyena")

class AdsbExchange:
    """adsb exchange API wrapper"""

    headers = {}
    in_queue = []
    out_dict = {}

    def __init__(self, api_key: str):
        self.api_key = api_key

        self.headers["X-RapidAPI-Key"] = api_key
        self.headers["X-RapidAPI-Host"] = "adsbexchange-com1.p.rapidapi.com"
        self.headers["Content-Type"] = "application/json"

    def janitor(self, value: str) -> str:
        """clean up string values"""

        temp = value.strip()
        if len(temp) < 1:
            return "unknown"

        return temp

    def parse_aircraft(self, args: dict[str, str]) -> dict[str, str]:
        """parse ADSB exchange API response"""

        if len(args) < 1:
            logger.info("skipping empty args")
            return {}

        if args["msg"] != "No error":
            logger.error(f"{args['msg']}")
            return {}

        if len(args["ac"]) < 1:
            logger.info("skipping empty aircraft list")
            return {}

        unwrapped = args["ac"]
        for ndx, _ in enumerate(unwrapped):
            results = {}

            temp = unwrapped[ndx]

            results["adsb_hex"] = temp["hex"].strip().lower()

            if "category" in temp:
                results["category"] = self.janitor(temp["category"])
            else:
                results["category"] = "none"

            if "emergency" in temp:
                results["emergency"] = self.janitor(temp["emergency"])
            else:
                results["emergency"] = "none"

            if "flight" in temp:
                results["flight"] = self.janitor(temp["flight"])
            else:
                results["flight"] = "unknown"

            if "r" in temp:
                results["registration"] = self.janitor(temp["r"])
            else:
                results["registration"] = "unknown"

            if "t" in temp:
                results["model"] = self.janitor(temp["t"])
            else:
                results["model"] = "unknown"

            results["ladd_flag"] = False
            results["military_flag"] = False
            results["pia_flag"] = False
            results["wierdo_flag"] = False

            if "dbFlags" in temp:
                db_flag = temp["dbFlags"]

                if db_flag & 1:
                    results["military_flag"] = True

                if db_flag & 2:
                    results["wierdo_flag"] = True

                if db_flag & 4:
                    results["pia_flag"] = True

                if db_flag & 8:
                    results["ladd_flag"] = True

            return results

    def fetch(self, adsb_hex: str) -> dict[str, any]:
        logger.info(f"fetching {adsb_hex} from ADSB exchange")

        try:
            # https://rapidapi.com/adsbx/api/adsbexchange-com1
            url = f"https://adsbexchange-com1.p.rapidapi.com/v2/icao/{adsb_hex}/"
            response = requests.get(url, headers=self.headers, timeout=5.0)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"skipping {adsb_hex} bad response {response.status_code}")
        except Exception as error:
            logger.error(error)
            
        return {}

    def execute(self, adsb_hex_list: list[str]) -> dict[str, dict[str, str]]:
        logger.info("adsb exchange execute")

        candidates = {}

        for adsb_hex in adsb_hex_list:
            key = adsb_hex.strip().lower()
            if key in candidates:
                logger.info(f"skipping duplicate {key}")
                continue

            raw = self.fetch(key)
            cooked = self.parse_aircraft(raw)
            if len(cooked) > 0:
                candidates[key] = cooked

        return candidates

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
            adsbx = AdsbExchange("bogus")
            adsbx.execute(["aa41f0","aadb37", "c0502e", "aadb35"])
        except yaml.YAMLError as error:
            logger.error(error)

# ;;; Local Variables: ***
# ;;; mode:python ***
# ;;; End: ***
