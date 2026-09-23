#
# Title: koala.py
# Description: generate koala files
# Development Environment: Ubuntu 22.04.5 LTS/python 3.10.12
# Author: G.S. Cole (guycole at gmail dot com)
#
import logging
import json
import os
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("koala")


class Koala:

    def __init__(self):
        self.koala_dir_adsb = os.environ.get("KOALA_DIR_ADSB", "/var/wombat/hyena/koala_adsb")
        self.koala_dir_uat = os.environ.get("KOALA_DIR_UAT", "/var/wombat/hyena/koala_uat")
        self.success_dir_adsb = os.environ.get("SUCCESS_DIR_ADSB", "/var/wombat/hyena/success_adsb")
        self.success_dir_uat = os.environ.get("SUCCESS_DIR_UAT", "/var/wombat/hyena/success_uat")

        # UID/GID are provided by container entrypoint; default keeps local behavior.
        self.wombat_uid = int(os.getenv("WOMBAT_UID", "1000"))
        self.wombat_gid = int(os.getenv("WOMBAT_GID", "1000"))

    def file_reader(self, file_name: str) -> bool:
        try:
            with open(file_name, "r", encoding="utf-8") as in_file:
                self.raw_buffer = json.load(in_file)
        except Exception as error:
            logger.error("file read failed for %s: %s", file_name, error)
            return False

        return True

    def file_writer(self, file_name: str, content: dict[str, Any]) -> bool:
        try:
            with open(file_name, "w", encoding="utf-8") as out_file:
                json.dump(content, out_file, indent=4)
                out_file.write("\n")
        except Exception as error:
            logger.error("file write failed for %s: %s", file_name, error)
            return False

        return True

    def file_processor(self, file_name: str) -> dict[str, Any]:
        if not self.file_reader(file_name):
            logger.warning("file read failed for %s", file_name)
            return {}

        result = {
            "epochSeconds": self.raw_buffer.get("timeStamp", {}).get("epochSeconds", 0),
            "geoLoc": {
                "site": self.raw_buffer.get("geoLoc", {}).get("siteName", "unknown")
            },
            "hostName": self.raw_buffer.get("equipment", {}).get("hostName", "unknown"),
            "project": self.raw_buffer.get("job", {}).get("project", "unknown"),
            "version": self.raw_buffer.get("version", 0),
            "observation": self.raw_buffer.get("observations", []),
            "adsbex": self.raw_buffer.get("adsbex", []),
        }

        return result

    def worker(self, koala_dir: str, success_dir: str) -> None:
        logger.info("koala dir: %s success dir:%s", koala_dir, success_dir)

        os.makedirs(koala_dir, exist_ok=True)
        if not os.path.isdir(success_dir):
            logger.warning("success dir missing: %s", success_dir)
            return

        os.chdir(success_dir)
        targets = [ff for ff in os.listdir(".") if ff.endswith(".json")]
        logger.info("%s files noted", len(targets))

        # koala only gets the most recent
        candidates = {}
        for target in targets:
            candidate = self.file_processor(target)
            if len(candidate) > 0:
                key = f"{candidate['epochSeconds']}.{candidate['hostName']}"
                candidates[key] = candidate

        winner = None
        for key in sorted(candidates):
            winner = candidates[key]

        if winner is None:
            logger.info("no winner found")
        else:
            out_file_name = os.path.join(
                koala_dir, f"{winner['epochSeconds']}.{winner['hostName']}"
            )
            self.file_writer(out_file_name, winner)
            os.chown(out_file_name, self.wombat_uid, self.wombat_gid)

    def execute(self) -> None:
        self.worker(self.koala_dir_adsb, self.success_dir_adsb)
        self.worker(self.koala_dir_uat, self.success_dir_uat)
      
if __name__ == "__main__":
    koala = Koala()
    koala.execute()

# ;;; Local Variables: ***
# ;;; mode:python ***
# ;;; End: ***
