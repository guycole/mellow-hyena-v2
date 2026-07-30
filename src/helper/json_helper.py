#
# Title: json_helper.py
# Description: JSON schema support
# Development Environment: Ubuntu 22.04.5 LTS/python 3.10.12
# Author: G.S. Cole (guycole at gmail dot com)
#
import json
import logging

from jsonschema import validate

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("json_helper")

schema = {
    "type": "object",
    "properties": {
        "equipment": {
            "type": "object",
            "properties": {
                "antenna":      {"type": "string"},
                "receiverId":   {"type": "number"},
                "receiverType": {"type": "string"},
                "hostName":     {"type": "string"},
                "hostType":     {"type": "string"},
            },
            "required": ["antenna", "receiverId", "receiverType", "hostName", "hostType"],
            "additionalProperties": False
        },
        "geoLoc": {
            "type": "object",
            "properties": {
                "altitude":  {"type": "number"},
                "latitude":  {"type": "number"},
                "longitude": {"type": "number"},
                "siteName":  {"type": "string"},
            },
            "required": ["altitude", "latitude", "longitude", "siteName"],
            "additionalProperties": False
        },
        "job": {
            "type": "object",
            "properties": {
                "mode":    {"type": "string"},
                "project": {"type": "string"},
                "task":    {"type": "string"},
            },
            "required": ["mode", "project", "task"],
            "additionalProperties": False
        },
        "timeStamp": {
            "type": "object",
            "properties": {
                "epochSeconds": {"type": "number"},
                "iso8601":      {"type": "string"},
            },
            "required": ["epochSeconds", "iso8601"],
            "additionalProperties": False
        },
        "crateName":    {"type": "string"},
        "fileName":     {"type": "string"},
        "version":      {"type": "number"},
        "adsbex": {
            "type": "object",
            "additionalProperties": {
                "type": "object",
                "properties": {
                    "adsb_hex":      {"type": "string"},
                    "category":      {"type": "string"},
                    "emergency":     {"type": "string"},
                    "flight":        {"type": "string"},
                    "registration":  {"type": "string"},
                    "model":         {"type": "string"},
                    "ladd_flag":     {"type": "boolean"},
                    "military_flag": {"type": "boolean"},
                    "pia_flag":      {"type": "boolean"},
                    "wierdo_flag":   {"type": "boolean"},
                },
                "required": ["adsb_hex", "category", "emergency", "flight", "registration", "model", "ladd_flag", "military_flag", "pia_flag", "wierdo_flag"],
                "additionalProperties": False
            }
        },
        "observations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "hex":       {"type": "string"},
                    "flight":    {"type": "string"},
                    "latitude":  {"type": "string"},
                    "longitude": {"type": "string"},
                    "altitude":  {"type": "string"},
                    "track":     {"type": "string"},
                    "speed":     {"type": "string"},
                },
                "required": ["hex", "flight", "latitude", "longitude", "altitude", "track", "speed"],
                "additionalProperties": False
            }
        },
    },
    "required": ["equipment", "geoLoc", "job", "timeStamp", "crateName", "fileName", "version", "adsbex", "observations"],
    "additionalProperties": False
}

class JsonHelper:

    def __init__(self):
        self.raw_json = None

    def json_file_reader(self, file_name: str, validate_flag: bool) -> bool:
        try:
            with open(file_name, "r", encoding="utf-8") as in_file:
                self.raw_json = json.load(in_file)
        except Exception as error:
            logger.error(f"file read failed for {file_name}: {error}")
            return False

        if validate_flag:
            try:
                validate(instance=self.raw_json, schema=schema)
            except Exception as error:
                logger.error(f"json validation failed for {file_name}: {error}")
                return False

        return True

    def json_file_writer(self, file_name: str, json_data: dict[str, any]) -> bool:
        try:
            validate(instance=json_data, schema=schema)
        except Exception as error:
            logger.error(f"json validation failed for {file_name}: {error.message}")
            return False

        try:
            with open(file_name, "w") as out_file:
                json.dump(json_data, out_file, indent=4)
        except Exception as error:
            logger.error(f"file write failure for {file_name}: {error}")
            return False

        return True

# ;;; Local Variables: ***
# ;;; mode:python ***
# ;;; End: ***
