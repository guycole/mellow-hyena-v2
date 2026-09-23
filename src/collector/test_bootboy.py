import io
import json

import yaml

from bootboy import BootBoy


def _admin_payload(task: str) -> dict[str, object]:
    return {
        "crateName": "wombat04",
        "hostName": "pi4h",
        "type": "rpi4",
        "geoLoc": {
            "altitude": 0,
            "latitude": 38.108,
            "longitude": -122.268,
            "siteName": "vallejo01",
        },
        "receiver": {
            "antenna": "multicoupler",
            "id": 12,
            "task": task,
            "type": "rtl-sdr-v4",
        },
    }


def _run_configuration(
    tmp_path, monkeypatch, receiver_task: str
) -> tuple[str, dict[str, object]]:
    admin_json = json.dumps(_admin_payload(receiver_task))

    def fake_path_open(self, mode="r", encoding=None):
        _ = encoding
        assert str(self).endswith(".json")
        assert mode == "r"
        return io.StringIO(admin_json)

    monkeypatch.setattr("bootboy.Path.open", fake_path_open)
    monkeypatch.chdir(tmp_path)

    bootboy = BootBoy()
    returned_task = bootboy.configuration("pi4h")

    with open("config.yaml", "r", encoding="utf-8") as in_file:
        generated = yaml.safe_load(in_file)

    return returned_task, generated


def test_configuration_for_dump978_writes_dump978_filename(
    tmp_path, monkeypatch
) -> None:
    returned_task, generated = _run_configuration(
        tmp_path, monkeypatch, "hyena-v2-dump978"
    )

    assert returned_task == "hyena-v2-dump978"
    assert generated["crateName"] == "wombat04"
    assert generated["freshDir"] == "/var/wombat/fresh/hyena"
    assert generated["receiver"]["task"] == "hyena-v2-dump978"
    assert generated["dump978Filename"] == "/tmp/aircraft.json"
    assert "dump1090Url" not in generated


def test_configuration_for_dump1090_writes_dump1090_url(tmp_path, monkeypatch) -> None:
    returned_task, generated = _run_configuration(
        tmp_path, monkeypatch, "hyena-v2-DUMP1090"
    )

    assert returned_task == "hyena-v2-DUMP1090"
    assert generated["crateName"] == "wombat04"
    assert generated["freshDir"] == "/var/wombat/fresh/hyena"
    assert generated["receiver"]["task"] == "hyena-v2-DUMP1090"
    assert generated["dump1090Url"] == "http://localhost:8080/data.json"
    assert "dump978Filename" not in generated
