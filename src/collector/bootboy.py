#
# Title: bootboy.py
# Description: generate configuration file
# Development Environment: Ubuntu 22.04.5 LTS/python 3.10.12
# Author: G.S. Cole (guycole at gmail dot com)
#
import datetime
import json
import socket
import sys
import time
import uuid
import zoneinfo

import yaml
from yaml.loader import SafeLoader

class BootBoy:

    def configuration(self, target: str) -> None:
        print(f"BootBoy: configuring {target}")

        # Build the path to the admin JSON file
        admin_json_path = f"/var/wombat/admin/{target}.json"

        try:
            with open(admin_json_path, "r") as f:
                config_data = json.load(f)
        except Exception as e:
            print(f"Error reading {admin_json_path}: {e}")
            sys.exit(1)

        # Compose new config dict for YAML output
        receiver = config_data.get("receiver", {})
        geoLoc = config_data.get("geoLoc", {})
        crateName = config_data.get("crateName", "xxx")
        hostName = config_data.get("hostName", target)
        type_val = config_data.get("type", "xxx")

        yaml_config = {
            "crateName": crateName,
            "dump1090url": "http://localhost:8080/data.json",
            "equipment": {
                "hostName": hostName,
                "type": type_val,
            },
            "receiver": {
                "antenna": receiver.get("antenna", "xxx"),
                "receiver_id": receiver.get("id", "xxx"),
                "type": receiver.get("type", "xxx"),
            },
            "freshDir": "/var/wombat/fresh/hyena",
            "geoLoc": geoLoc,
        }

        # Write to config.yaml in the current directory
        try:
            with open("config.yaml", "w") as f:
                yaml.dump(yaml_config, f, default_flow_style=False)
            print("config.yaml generated successfully.")
        except Exception as e:
            print(f"Error writing config.yaml: {e}")
            sys.exit(1)

    def crontab(self) -> None:
        import subprocess
        crontab_entry = "* * * * * /home/wombat/Documents/github/mellow-hyena-v2/bin/adsb-collector.sh > /dev/null 2>&1"

        try:
            # Always operate on the 'wombat' user's crontab
            result = subprocess.run(["crontab", "-u", "wombat", "-l"], capture_output=True, text=True)
            if result.returncode == 0:
                current_crontab = result.stdout.splitlines()
            else:
                current_crontab = []
        except Exception as e:
            print(f"Error reading wombat's crontab: {e}")
            return

        # Check if entry already exists
        if any(crontab_entry in line for line in current_crontab):
            print("Crontab entry already exists for wombat.")
            return

        # Add the new entry
        current_crontab.append(crontab_entry)
        new_crontab = "\n".join(current_crontab) + "\n"
        try:
            proc = subprocess.run(["crontab", "-u", "wombat", "-"], input=new_crontab, text=True)
            if proc.returncode == 0:
                print("Crontab updated successfully for wombat.")
            else:
                print("Failed to update wombat's crontab.")
        except Exception as e:
            print(f"Error updating wombat's crontab: {e}")

    def execute(self, target: str) -> None:
        self.configuration(target)
        #self.crontab()

#
# 
#
if __name__ == "__main__":
    target = socket.gethostname()
    target = "pi4k"

    bb = BootBoy()
    bb.execute(target)

# ;;; Local Variables: ***
# ;;; mode:python ***
# ;;; End: ***