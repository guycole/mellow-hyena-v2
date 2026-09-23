#
# Title: bootboy.py
# Description: generate configuration file
# Development Environment: Ubuntu 22.04.5 LTS/python 3.10.12
# Author: G.S. Cole (guycole at gmail dot com)
#
import json
import os
import platform
import socket
import subprocess
import sys
import time
from pathlib import Path

import yaml

CONFIG_FILE_NAME = "config.yaml"
CRONTAB_ENTRY = (
    "* * * * * $HOME/github/mellow-hyena-v2/bin/collector.sh > /dev/null 2>&1"
)


class BootBoy:

    def can_manage_systemd(self, service_name: str) -> bool:
        if platform.system() != "Linux":
            print(f"{service_name} management skipped on non-Linux host.")
            return False

        if os.geteuid() != 0:
            print(
                f"{service_name} management skipped: "
                "must run as root (systemd boot path)."
            )
            return False

        return True

    def run_systemctl(self, action: str, service_name: str) -> tuple[int, str]:
        # Use --no-block for start so systemd queues the job and returns
        # immediately, preventing a deadlock when bootboy itself runs under systemd.
        cmd = (
            ["systemctl", "--no-block", action, service_name]
            if action == "start"
            else ["systemctl", action, service_name]
        )
        proc = subprocess.run(cmd, capture_output=True, text=True)
        stderr = proc.stderr.strip()
        return proc.returncode, stderr

    def configuration(self, target: str) -> str:
        print(f"BootBoy: configuring {target}")

        # Build the path to the admin JSON file
        admin_json_path = Path(f"/var/wombat/admin/{target}.json")

        try:
            with admin_json_path.open("r", encoding="utf-8") as admin_file:
                config_data = json.load(admin_file)
        except Exception as error:
            print(f"Error reading {admin_json_path}: {error}")
            sys.exit(1)

        # Compose new config dict for YAML output
        crate_name = config_data.get("crateName", "xxx")
        geo_loc = config_data.get("geoLoc", {})
        host_name = config_data.get("hostName", target)
        host_type = config_data.get("type", "xxx")
        receiver = config_data.get("receiver", {})

        yaml_config = {
            "crateName": crate_name,
            "freshDir": "/var/wombat/fresh/hyena",
            "equipment": {
                "hostName": host_name,
                "hostType": host_type,
            },
            "geoLoc": geo_loc,
            "receiver": {
                "antenna": receiver.get("antenna", "xxx"),
                "receiverId": receiver.get("id", "xxx"),
                "task": receiver.get("task", "xxx"),
                "type": receiver.get("type", "xxx"),
            },
        }

        task_name = str(receiver.get("task", "xxx"))
        task_name_lc = task_name.lower()
        if "dump978" in task_name_lc:
            yaml_config["dump978Filename"] = "/tmp/aircraft.json"
        else:
            yaml_config["dump1090Url"] = "http://localhost:8080/data.json"

        # Write to config.yaml in the current directory
        try:
            with open(CONFIG_FILE_NAME, "w", encoding="utf-8") as config_file:
                yaml.dump(
                    yaml_config,
                    config_file,
                    default_flow_style=False,
                    sort_keys=False,
                )
            print(f"{CONFIG_FILE_NAME} generated successfully.")
        except Exception as error:
            print(f"Error writing {CONFIG_FILE_NAME}: {error}")
            sys.exit(1)

        return task_name

    def verify_service_active(self, service_name: str) -> None:
        # --no-block returns immediately; give systemd a moment to actually
        # start (or fail to start) the service before checking.
        time.sleep(2)
        returncode, _ = self.run_systemctl("is-active", service_name)
        if returncode == 0:
            print(f"{service_name} is active.")
        else:
            print(
                f"{service_name} is NOT active after start; "
                f"check: journalctl -u {service_name}"
            )

    def manage_dump1090(self, receiver_task: str) -> None:
        if "dump1090" not in receiver_task.lower():
            print("dump1090.service not managed for non-ADSB receiver task.")
            return

        if not self.can_manage_systemd("dump1090.service"):
            print(
                "dump1090.service not managed because systemd cannot "
                "be managed on this system."
            )
            return

        # Only start — never enable. dump1090 must not auto-start at boot;
        # bootboy.py is the sole entry point that starts this service.
        print("starting dump1090 service")
        returncode, stderr = self.run_systemctl("start", "dump1090.service")
        if returncode == 0:
            print("dump1090.service start queued.")
            self.verify_service_active("dump1090.service")
        else:
            print(f"Failed to start dump1090.service: {stderr}")

    def manage_dump978(self, receiver_task: str) -> None:
        if "dump978" not in receiver_task.lower():
            print("dump978.service not managed for non-UAT receiver task.")
            return

        if not self.can_manage_systemd("dump978.service"):
            print(
                "dump978.service not managed because systemd cannot "
                "be managed on this system."
            )
            return

        # Only start — never enable. dump978 must not auto-start at boot;
        # bootboy.py is the sole entry point that starts this service.
        print("starting dump978 service")
        returncode, stderr = self.run_systemctl("start", "dump978.service")
        if returncode == 0:
            print("dump978.service start queued.")
            self.verify_service_active("dump978.service")
        else:
            print(f"Failed to start dump978.service: {stderr}")

    def crontab(self) -> None:
        # Always overwrite — wombat is dedicated to this workload and must have
        # exactly one cron entry.  This removes any stale entries unconditionally.
        new_crontab = CRONTAB_ENTRY + "\n"
        try:
            proc = subprocess.run(
                ["crontab", "-u", "wombat", "-"],
                input=new_crontab,
                text=True,
                capture_output=True,
            )
            if proc.returncode == 0:
                print("crontab updated for wombat.")
            else:
                stderr = proc.stderr.strip() or "no stderr"
                print(f"Failed to update wombat crontab: {stderr}")
        except Exception as error:
            print(f"Error updating wombat crontab: {error}")

    def execute(self, target: str) -> None:
        task = self.configuration(target)
        self.crontab()
        self.manage_dump1090(task)
        self.manage_dump978(task)

#
if __name__ == "__main__":
    target = socket.gethostname()
    # target = "pi4k"

    bb = BootBoy()
    bb.execute(target)

# ;;; Local Variables: ***
# ;;; mode:python ***
# ;;; End: ***
