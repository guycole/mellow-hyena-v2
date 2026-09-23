import json
import uuid

from collector import HyenaCollector, TimeStamp


def _write_dump978(path: str) -> None:
    payload = {
        "aircraft": [
            {
                "hex": "aa11bb",
                "flight": "HYENA1",
                "lat": 38.054087,
                "lon": -122.45445,
                "altitude": 4400,
                "track": 322,
                "speed": 99,
            }
        ]
    }
    with open(path, "w", encoding="utf-8") as out_file:
        json.dump(payload, out_file)


def _config(fresh_dir: str, dump978_filename: str) -> dict[str, object]:
    return {
        "crateName": "demo-crate",
        "freshDir": fresh_dir,
        "equipment": {
            "hostName": "demo-host",
            "hostType": "laptop",
        },
        "geoLoc": {
            "altitude": 100.0,
            "latitude": 42.0,
            "longitude": -71.0,
            "siteName": "demo-site",
        },
        "receiver": {
            "antenna": "dipole",
            "receiverId": 7,
            "task": "hyena-v2-dump978",
            "type": "rtl-sdr-v4",
        },
        "dump978Filename": dump978_filename,
    }


def test_timestamp_syncs_iso8601_from_epoch_seconds() -> None:
    stamp = TimeStamp(epoch_seconds=0)

    assert stamp.iso8601 == "1970-01-01T00:00:00+00:00"


def test_hyena_collector_derives_job_from_receiver_task(tmp_path) -> None:
    dump978_path = tmp_path / "aircraft.json"
    _write_dump978(str(dump978_path))

    collector = HyenaCollector(_config(str(tmp_path), str(dump978_path)))

    assert collector.job.mode == "dump978"
    assert collector.job.project == "hyena-v2"
    assert collector.job.task == "hyena-v2-dump978"


def test_execute_writes_expected_payload_file(tmp_path, monkeypatch) -> None:
    fixed_uuid = uuid.UUID("5cc9fa9d-5065-400e-b578-76633bdd3699")
    monkeypatch.setattr("collector.uuid.uuid4", lambda: fixed_uuid)

    dump978_path = tmp_path / "aircraft.json"
    _write_dump978(str(dump978_path))

    collector = HyenaCollector(_config(str(tmp_path), str(dump978_path)))
    collector.time_stamp = TimeStamp(epoch_seconds=0)

    result = collector.execute()

    assert result == 0

    output_path = tmp_path / f"{fixed_uuid}.json"
    assert output_path.exists()

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["crateName"] == "demo-crate"
    assert payload["fileName"] == f"{fixed_uuid}.json"
    assert payload["job"]["mode"] == "dump978"
    assert payload["job"]["project"] == "hyena-v2"
    assert payload["timeStamp"]["epochSeconds"] == 0
    assert payload["timeStamp"]["iso8601"] == "1970-01-01T00:00:00+00:00"
    assert payload["adsbex"] == {}
    assert len(payload["observations"]) == 1
