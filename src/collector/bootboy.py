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
import sys

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
        # Use --no-block for start so systemd queues the job and returns
        # immediately, preventing a deadlock when bootboy itself runs under systemd.
        cmd = ["systemctl", "--no-block", action, service_name] if action == "start" else ["systemctl", action, service_name]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        stderr = proc.stderr.strip()
        return proc.returncode, stderr

    def configuration(self, target: str) -> dict[str, any]:
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
        crate_name = config_data.get("crateName", "xxx")
        geo_loc = config_data.get("geoLoc", {})
        host_name = config_data.get("hostName", target)
        host_type = config_data.get("type", "xxx")
        receiver = config_data.get("receiver", {})

        yaml_config = {
            "crateName": crate_name,
            "equipment": {
                "hostName": host_name,
                "hostType": host_type,
            },
            "receiver": {
                "antenna": receiver.get("antenna", "xxx"),
                "receiverId": receiver.get("id", "xxx"),
                "task": receiver.get("task", "xxx"),
                "type": receiver.get("type", "xxx"),
            },
            "freshDir": "/var/wombat/fresh/hyena",
            "geoLoc": geo_loc,
            "gpsEnable": False,
        }

        if receiver["task"].endswith("dump978"):
            yaml_config["dump978Filename"] = "/tmp/aircraft.json"
        else:
            yaml_config["dump1090Url"] = "http://localhost:8080/data.json"

        # Write to config.yaml in the current directory
        try:
            with open("config.yaml", "w") as f:
                yaml.dump(yaml_config, f, default_flow_style=False)
            print("config.yaml generated successfully.")
        except Exception as e:
            print(f"Error writing config.yaml: {e}")
            sys.exit(1)

        return yaml_config

    def verify_service_active(self, service_name: str) -> None:
        import time
        # --no-block returns immediately; give systemd a moment to actually
        # start (or fail to start) the service before checking.
        time.sleep(2)
        returncode, _ = self.run_systemctl("is-active", service_name)
        if returncode == 0:
            print(f"{service_name} is active.")
        else:
            print(f"{service_name} is NOT active after start — check: journalctl -u {service_name}")

    def manage_dump1090(self, receiver_task: str) -> None:
        if "dump1090" not in receiver_task.lower():
            print("dump1090.service not managed for non-ADSB receiver task.")
            return

        if not self.can_manage_systemd("dump1090.service"):
            print("dump1090.service not managed because systemd cannot be managed on this system.")
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
            print("dump978.service not managed because systemd cannot be managed on this system.")
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
        import subprocess
        crontab_entry = "* * * * * $HOME/github/mellow-hyena-v2/bin/collector.sh > /dev/null 2>&1"

        # Always overwrite — wombat is dedicated to this workload and must have
        # exactly one cron entry.  This removes any stale entries unconditionally.
        new_crontab = crontab_entry + "\n"
        try:
            proc = subprocess.run(["crontab", "-u", "wombat", "-"], input=new_crontab, text=True)
            if proc.returncode == 0:
                print("crontab updated for wombat.")
            else:
                print("Failed to update wombat crontab.")
        except Exception as e:
            print(f"Error updating wombat crontab: {e}")

    def execute(self, target: str) -> None:
        config = self.configuration(target)
        self.crontab()
        self.manage_dump1090(config["receiver"]["task"])
        self.manage_dump978(config["receiver"]["task"])

#
if __name__ == "__main__":
    target = socket.gethostname()
    #target = "pi4k"

    bb = BootBoy()
    bb.execute(target)

# ;;; Local Variables: ***
# ;;; mode:python ***
# ;;; End: ***
