#
# Title: json_helper.py
# Description: JSON schema support
# Development Environment: Ubuntu 22.04.5 LTS/python 3.10.12
# Author: G.S. Cole (guycole at gmail dot com)
#
import json
import logging
from typing import Any

from jsonschema import validate
from jsonschema.exceptions import ValidationError

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("json_helper")

schema = {
    "type": "object",
    "properties": {
        "equipment": {
            "type": "object",
            "properties": {
                "hostName":     {"type": "string"},
                "hostType":     {"type": "string"},
            },
            "required": ["hostName", "hostType"],
            "additionalProperties": False
        },
        "receiver": {
            "type": "object",
            "properties": {
                "antenna":    {"type": "string"},
                "receiverId": {"type": "number"},
                "task":       {"type": "string"},
                "type":       {"type": "string"},
            },
            "required": ["antenna", "receiverId", "task", "type"],
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
        "sourceFileName": {"type": "string"},
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
    "required": ["equipment", "geoLoc", "job", "receiver", "timeStamp", "crateName", "fileName", "version", "adsbex", "observations"],
    "additionalProperties": False
}

class JsonHelper:

    def __init__(self, app_logger: logging.Logger | None = None):
        self.logger = app_logger or logger
        self.raw_json = None

    def json_file_reader(self, file_name: str, validate_flag: bool) -> bool:
        try:
            with open(file_name, "r", encoding="utf-8") as in_file:
                self.raw_json = json.load(in_file)
        except (OSError, json.JSONDecodeError) as error:
            self.logger.error("file read failed for %s: %s", file_name, error)
            return False

        if validate_flag:
            try:
                validate(instance=self.raw_json, schema=schema)
            except ValidationError as error:
                # error.json_path pinpoints which array/object entry actually failed
                path = getattr(error, "json_path", None) or str(getattr(error, "absolute_path", ""))
                self.logger.error(
                    "json validation failed for %s: %s at %s",
                    file_name,
                    error.message,
                    path,
                )
                return False

        return True

    def json_file_writer(self, file_name: str, json_data: dict[str, Any]) -> bool:
        try:
            validate(instance=json_data, schema=schema)
        except ValidationError as error:
            path = getattr(error, "json_path", None) or str(getattr(error, "absolute_path", ""))
            self.logger.error(
                "json validation failed for %s: %s at %s",
                file_name,
                error.message,
                path,
            )
            return False

        try:
            with open(file_name, "w", encoding="utf-8") as out_file:
                json.dump(json_data, out_file, indent=4)
        except OSError as error:
            self.logger.error("file write failure for %s: %s", file_name, error)
            return False

        return True

# ;;; Local Variables: ***
# ;;; mode:python ***
# ;;; End: ***
