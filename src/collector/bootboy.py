#
# Title: bootboy.py
# Description: generate configuration file
# Development Environment: Ubuntu 22.04.5 LTS/python 3.10.12
# Author: G.S. Cole (guycole at gmail dot com)
#
import datetime
import json
import os
import platform
import socket
import sys
import time
import uuid
import zoneinfo

import yaml
from yaml.loader import SafeLoader

class BootBoy:

    def can_manage_systemd(self, service_name: str) -> bool:
        if platform.system() != "Linux":
            print(f"{service_name} management skipped on non-Linux host.")
            return False

        if os.geteuid() != 0:
            print(f"{service_name} management skipped: must run as root (systemd boot path).")
            return False

        return True

    def run_systemctl(self, action: str, service_name: str) -> tuple[int, str]:
        import subprocess
        cmd = ["systemctl", action, service_name]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        stderr = proc.stderr.strip()
        return proc.returncode, stderr

    def configuration(self, target: str) -> dict[str, str]:
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
        geo_loc = config_data.get("geoLoc", {})
        crate_name = config_data.get("crateName", "xxx")
        host_name = config_data.get("hostName", target)
        host_type = config_data.get("type", "xxx")

        yaml_config = {
            "crateName": crate_name,
            "dump978filename": "/tmp/aircraft.json",
            "dump1090url": "http://localhost:8080/data.json",
            "host": {
                "name": host_name,
                "type": host_type,
            },
            "receiver": {
                "antenna": receiver.get("antenna", "xxx"),
                "receiver_id": receiver.get("id", "xxx"),
                "task": receiver.get("task", "xxx"),
                "type": receiver.get("type", "xxx"),
            },
            "freshDir": "/var/wombat/fresh/hyena",
            "geoLoc": geo_loc,
        }

        # Write to config.yaml in the current directory
        try:
            with open("config.yaml", "w") as f:
                yaml.dump(yaml_config, f, default_flow_style=False)
            print("config.yaml generated successfully.")
        except Exception as e:
            print(f"Error writing config.yaml: {e}")
            sys.exit(1)

        return {
            "receiver_task": receiver.get("task", "xxx"),
            "host_type": host_type,
        }

    def manage_systemd_service(self, service_name: str, receiver_task: str, task_name: str) -> None:
        if not self.can_manage_systemd(service_name):
            return

        if task_name not in receiver_task.lower():
            print(f"{service_name} not managed for non-{task_name.upper()} receiver task.")
            return

        for action in ("enable", "start"):
            try:
                returncode, stderr = self.run_systemctl(action, service_name)
            except Exception as e:
                print(f"Error managing {service_name}: {e}")
                return

            if returncode == 0:
                print(f"{service_name} {action}d successfully.")
            else:
                print(f"Failed to {action} {service_name}: {stderr}")
                return

    def start_systemd_service(self, service_name: str) -> None:
        if not self.can_manage_systemd(service_name):
            return

        for action in ("enable", "start"):
            try:
                returncode, stderr = self.run_systemctl(action, service_name)
            except Exception as e:
                print(f"Error managing {service_name}: {e}")
                return

            if returncode == 0:
                print(f"{service_name} {action}d successfully.")
            else:
                print(f"Failed to {action} {service_name}: {stderr}")
                return

    def manage_dump1090(self, receiver_task: str, host_type: str) -> None:
        if "adsb" in receiver_task.lower():
            self.start_systemd_service("dump1090.service")
            return

        self.manage_systemd_service("dump1090.service", receiver_task, "adsb")

    def manage_dump978(self, receiver_task: str) -> None:
        if "uat" in receiver_task.lower():
            self.start_systemd_service("dump978.service")
            return

        self.manage_systemd_service("dump978.service", receiver_task, "uat")

    def crontab(self) -> None:
        import subprocess
        crontab_entry = "* * * * * /home/wombat/Documents/github/mellow-hyena-v2/bin/collector.sh > /dev/null 2>&1"

        try:
            # The wombat user is dedicated to this workload.
            # Enforce exactly one current cron entry to remove stale lines.
            result = subprocess.run(["crontab", "-u", "wombat", "-l"], capture_output=True, text=True)
            if result.returncode == 0:
                current_crontab = [line.strip() for line in result.stdout.splitlines() if line.strip()]
            else:
                current_crontab = []
        except Exception as e:
            print(f"Error reading wombat's crontab: {e}")
            return

        desired_crontab = [crontab_entry]

        # Skip write if already exactly correct.
        if current_crontab == desired_crontab:
            print("Crontab entry already exists for wombat.")
            return

        new_crontab = "\n".join(desired_crontab) + "\n"
        try:
            proc = subprocess.run(["crontab", "-u", "wombat", "-"], input=new_crontab, text=True)
            if proc.returncode == 0:
                print("Crontab replaced successfully for wombat.")
            else:
                print("Failed to update wombat's crontab.")
        except Exception as e:
            print(f"Error updating wombat's crontab: {e}")

    def execute(self, target: str) -> None:
        config = self.configuration(target)
        self.crontab()
        self.manage_dump1090(config["receiver_task"], config["host_type"])
        self.manage_dump978(config["receiver_task"])

#
# 
#
if __name__ == "__main__":
    target = socket.gethostname()
    #target = "pi4k"

    bb = BootBoy()
    bb.execute(target)

# ;;; Local Variables: ***
# ;;; mode:python ***
# ;;; End: ***
