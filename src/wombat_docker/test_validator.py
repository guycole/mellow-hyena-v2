import logging

from validator import HyenaValidator


class FakeGeoLoc:
    def __init__(self, identifier: int):
        self.id = identifier


class FakePostgres:
    def __init__(self):
        self.selected = None
        self.inserted = []
        self.daily_scored = []

    def load_log_select_by_file_name(self, _file_name):
        return self.selected

    def geo_loc_select_by_site(self, _site_name):
        return [FakeGeoLoc(7)]

    def load_log_insert(self, load_log):
        self.inserted.append(load_log)

    def daily_score_insert_or_update(self, daily_score):
        self.daily_scored.append(daily_score)


def _validator() -> tuple[HyenaValidator, FakePostgres]:
    postgres = FakePostgres()
    validator = HyenaValidator(logging.getLogger("test"), postgres)
    return validator, postgres


def _raw_json(mode: str = "dump1090") -> dict:
    return {
        "timeStamp": {"epochSeconds": 1, "iso8601": "1970-01-01T00:00:01+00:00"},
        "equipment": {"hostName": "host-a"},
        "observations": [{"hex": "abc123"}],
        "job": {"project": "hyena-v2", "mode": mode, "task": f"hyena-v2-{mode}"},
        "geoLoc": {"siteName": "site-a"},
        "crateName": "crate-a",
        "adsbex": {},
        "version": 1,
    }


def test_load_log_test_inserts_when_not_previously_processed() -> None:
    validator, postgres = _validator()
    validator.json_helper.raw_json = _raw_json(mode="dump1090")

    result = validator.load_log_test("abc.json")

    assert result is True
    assert len(postgres.inserted) == 1
    assert len(postgres.daily_scored) == 1
    assert postgres.inserted[0]["file_name"] == "abc.json"
    assert postgres.inserted[0]["epoch_seconds"] == 1


def test_file_processor_success_path(monkeypatch) -> None:
    validator, _postgres = _validator()

    monkeypatch.setattr(validator.json_helper, "json_file_reader", lambda _name, _flag: True)
    validator.json_helper.raw_json = _raw_json(mode="dump978")
    monkeypatch.setattr(validator, "load_log_test", lambda _name: True)

    calls = {"success": 0, "failure": 0}
    monkeypatch.setattr(
        validator,
        "file_success",
        lambda _name: calls.__setitem__("success", calls["success"] + 1),
    )
    monkeypatch.setattr(
        validator,
        "file_failure",
        lambda _name: calls.__setitem__("failure", calls["failure"] + 1),
    )
    monkeypatch.setattr("validator.os.path.isfile", lambda _path: True)
    monkeypatch.setattr("validator.os.path.getsize", lambda _path: 10)

    result = validator.file_processor("ok.json")

    assert result is True
    assert calls["success"] == 1
    assert calls["failure"] == 0


def test_execute_processes_all_targets(monkeypatch) -> None:
    validator, _postgres = _validator()

    monkeypatch.setattr("validator.os.path.isdir", lambda _path: True)
    monkeypatch.setattr("validator.os.chdir", lambda _path: None)
    monkeypatch.setattr("validator.os.listdir", lambda _path: ["b.json", "a.json"])

    seen = []
    monkeypatch.setattr(validator, "file_processor", lambda name: seen.append(name) or True)

    result = validator.execute()

    assert result == 0
    assert seen == ["a.json", "b.json"]


def test_file_processor_already_processed_counts_as_skip(monkeypatch) -> None:
    validator, postgres = _validator()
    postgres.selected = object()

    monkeypatch.setattr(validator.json_helper, "json_file_reader", lambda _name, _flag: True)
    validator.json_helper.raw_json = _raw_json(mode="dump1090")
    monkeypatch.setattr("validator.os.path.isfile", lambda _path: True)
    monkeypatch.setattr("validator.os.path.getsize", lambda _path: 10)

    result = validator.file_processor("dupe.json")

    assert result is False
    assert validator.skipped == 1
    assert validator.failure == 0
