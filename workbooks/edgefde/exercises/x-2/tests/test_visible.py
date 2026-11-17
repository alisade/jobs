import run
import sensor


def test_faulty_stream_alerts():
    assert sum(r.alert for r in run.run(sensor.stream(10, seed=1, fault_hz=105.75))) >= 8


def test_healthy_stream_is_quiet():
    res = run.run(sensor.stream(10, seed=1))
    assert sum(r.alert for r in res) == 0, [round(r.kurtosis, 1) for r in res]
