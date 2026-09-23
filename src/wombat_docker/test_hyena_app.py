import hyena_app


class FakeValidator:
    def __init__(self, _logger, _postgres):
        pass

    def execute(self) -> int:
        return 0


class FakeKoala:
    def execute(self) -> None:
        return None


def test_execute_runs_validator_mode(monkeypatch) -> None:
    monkeypatch.setattr(hyena_app, "HyenaValidator", FakeValidator)

    app = hyena_app.HyenaApp("validator")

    assert app.execute() == 0


def test_execute_runs_koala_mode(monkeypatch) -> None:
    monkeypatch.setattr(hyena_app, "Koala", FakeKoala)

    app = hyena_app.HyenaApp("koala")

    assert app.execute() == 0


def test_execute_rejects_invalid_mode() -> None:
    app = hyena_app.HyenaApp("bad-mode")

    assert app.execute() == 1
