"""adsb exchange API wrapper"""

import logging
import sys
from typing import Any

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("hyena")


class AdsbExchange:
    """adsb exchange API wrapper"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers: dict[str, str] = {}

        self.headers["X-RapidAPI-Key"] = api_key
        self.headers["X-RapidAPI-Host"] = "adsbexchange-com1.p.rapidapi.com"
        self.headers["Content-Type"] = "application/json"

    @staticmethod
    def janitor(value: str | None) -> str:
        """clean up string values"""

        temp = (value or "").strip()
        if len(temp) < 1:
            return "unknown"

        return temp

    def parse_aircraft(self, args: dict[str, Any]) -> dict[str, Any]:
        """parse ADSB exchange API response"""

        if len(args) < 1:
            logger.info("skipping empty args")
            return {}

        if args.get("msg") != "No error":
            logger.error("%s", args.get("msg", "unknown API error"))
            return {}

        aircraft = args.get("ac")
        if not isinstance(aircraft, list) or len(aircraft) < 1:
            logger.info("skipping empty aircraft list")
            return {}

        temp = aircraft[0]
        results: dict[str, Any] = {}
        results["adsb_hex"] = self.janitor(temp.get("hex")).lower()
        results["category"] = self.janitor(temp.get("category", "none"))
        results["emergency"] = self.janitor(temp.get("emergency", "none"))
        results["flight"] = self.janitor(temp.get("flight", "unknown"))
        results["registration"] = self.janitor(temp.get("r", "unknown"))
        results["model"] = self.janitor(temp.get("t", "unknown"))

        results["ladd_flag"] = False
        results["military_flag"] = False
        results["pia_flag"] = False
        results["wierdo_flag"] = False

        db_flag = temp.get("dbFlags", 0)
        if isinstance(db_flag, int):
            if db_flag & 1:
                results["military_flag"] = True

            if db_flag & 2:
                results["wierdo_flag"] = True

            if db_flag & 4:
                results["pia_flag"] = True

            if db_flag & 8:
                results["ladd_flag"] = True

        return results

    def fetch(self, adsb_hex: str) -> dict[str, Any]:
        logger.info("fetching %s from ADSB exchange", adsb_hex)

        try:
            # https://rapidapi.com/adsbx/api/adsbexchange-com1
            url = f"https://adsbexchange-com1.p.rapidapi.com/v2/icao/{adsb_hex}/"
            response = requests.get(url, headers=self.headers, timeout=5.0)
            if response.status_code == 200:
                return response.json()

            logger.error("skipping %s bad response %s", adsb_hex, response.status_code)
        except requests.RequestException as error:
            logger.error("fetch failed for %s: %s", adsb_hex, error)

        return {}

    def execute(self, adsb_hex_list: list[str]) -> dict[str, dict[str, Any]]:
        logger.info("adsb exchange execute")

        candidates: dict[str, dict[str, Any]] = {}

        for adsb_hex in adsb_hex_list:
            key = adsb_hex.strip().lower()
            if key in candidates:
                logger.info("skipping duplicate %s", key)
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
    _ = sys.argv
    adsbx = AdsbExchange("bogus")
    adsbx.execute(["aa41f0", "aadb37", "c0502e", "aadb35"])

# ;;; Local Variables: ***
# ;;; mode:python ***
# ;;; End: ***
