import time
import statistics

from timequota import TimeQuota


def test_init():
    # init
    tq = TimeQuota(5, "s", name="init")

    assert tq.quota == 5.0
    assert tq.unit == "s"
    assert tq.display_unit == "s"
    assert tq.name == "init"

    assert tq.time_since != 0

    assert tq.time_elapsed == 0
    assert tq.time_remaining == 5.0
    assert tq.overflow == False
    assert tq.predicted_overflow == False
    assert tq.time_exceeded == False
    assert tq.time_steps == []
    assert tq.time_per_step == 0
    assert tq.time_this_step == 0

    assert tq.step_aggr_fn == statistics.mean
    assert tq.timer_fn == time.perf_counter
    assert tq.logger_fn == print
    assert tq.precision == 4
    assert any(tq._color_dict.values())
    assert tq.verbose == True

    # minutes
    tq = TimeQuota(5, "m", name="init-minutes", verbose=False)
    assert tq.unit == "m"
    assert tq.display_unit == "m"
    assert tq.quota == 5.0 * 60

    # hours
    tq = TimeQuota(5, "h", name="init-minutes", verbose=False)
    assert tq.unit == "h"
    assert tq.display_unit == "h"
    assert tq.quota == 5.0 * (60 * 60)

    # infinite
    tq = TimeQuota(float("inf"), name="init-infinite", verbose=False)
    assert tq.quota == float("inf")

    # custom params
    tq = TimeQuota(
        26,
        "m",
        "p",
        name="init-custom",
        step_aggr_fn=statistics.geometric_mean,
        timer_fn=time.thread_time,
        logger_fn=None,
        precision=2,
        color=False,
        verbose=False,
    )

    assert tq.quota == 26.0 * 60
    assert tq.unit == "m"
    assert tq.display_unit == "p"
    assert tq.name == "init-custom"

    assert tq.time_since != 0

    assert tq.time_elapsed == 0
    assert tq.time_remaining == 26.0 * 60
    assert tq.overflow == False
    assert tq.predicted_overflow == False
    assert tq.time_exceeded == False
    assert tq.time_steps == []
    assert tq.time_per_step == 0
    assert tq.time_this_step == 0

    assert tq.step_aggr_fn == statistics.geometric_mean
    assert tq.timer_fn == time.thread_time
    assert tq.logger_fn is None
    assert tq.precision == 2
    assert not any(tq._color_dict.values())
    assert tq.verbose == False


def test_reset():
    tq = TimeQuota(5, "s", name="reset")

    # update attributes
    tq.time_elapsed = 10
    tq.time_remaining = 10
    tq.overflow = True
    tq.time_this_step = 10

    assert tq.time_elapsed == 10
    assert tq.time_remaining == 10
    assert tq.overflow == True
    assert tq.time_this_step == 10

    # reset
    tq.reset()
    assert tq.time_elapsed == 0
    assert tq.time_remaining == 5.0
    assert tq.overflow == False
    assert tq.time_this_step == 0


def test_update():
    tq = TimeQuota(1, "s", name="update", verbose=False)

    # time not exhausted
    tq.reset()
    time.sleep(0.5)
    tq.update()
    assert tq.overflow == False
    assert tq.predicted_overflow == False
    assert tq.time_exceeded == False

    # time exhausted
    tq.reset()
    time.sleep(1.5)
    tq.update()
    assert tq.overflow == True
    assert tq.predicted_overflow == False
    assert tq.time_exceeded == True


def test_track():
    tq = TimeQuota(1, "s", name="track", verbose=False)

    # time not exhausted
    tq.reset()
    time.sleep(0.2)
    tq.track()
    assert tq.overflow == False
    assert tq.predicted_overflow == False
    assert tq.time_exceeded == False
    assert 0.15 < tq.time_this_step < 0.25
    assert 0.15 < tq.time_per_step < 0.25

    # time predicted exhausted
    tq.reset()
    time.sleep(0.6)
    tq.track()
    assert tq.overflow == False
    assert tq.predicted_overflow == True
    assert tq.time_exceeded == True
    assert 0.55 < tq.time_this_step < 0.65
    assert 0.55 < tq.time_per_step < 0.65

    # time exhausted
    tq.reset()
    time.sleep(1)
    tq.track()
    assert tq.overflow == True
    assert tq.predicted_overflow == True
    assert tq.time_exceeded == True
    assert 0.95 < tq.time_this_step < 1.05
    assert 0.95 < tq.time_per_step < 1.05


def test_iter():
    tq = TimeQuota(3, "s", name="range", verbose=False)
    iterable = list("abc")

    # function
    assert list(tq.iter(iterable)) == iterable

    # time pre-exhausted
    tq.reset()
    time.sleep(5)
    for _ in tq.iter(iterable):
        pass
    assert tq.overflow == True
    assert tq.predicted_overflow == False
    assert tq.time_exceeded == True

    # time not exhausted
    tq.reset()
    for _ in tq.iter(iterable):
        time.sleep(0.5)
    assert tq.overflow == False
    assert tq.predicted_overflow == False
    assert tq.time_exceeded == False
    assert 0.45 < tq.time_this_step < 0.55
    assert 0.45 < tq.time_per_step < 0.55

    # time predicted exhausted
    tq.reset()
    for _ in tq.iter(iterable):
        time.sleep(1.7)
    assert tq.overflow == False
    assert tq.predicted_overflow == True
    assert tq.time_exceeded == True
    assert 1.65 < tq.time_this_step < 1.75
    assert 1.65 < tq.time_per_step < 1.75

    # time exhausted
    tq.reset()
    for _ in tq.iter(iterable):
        time.sleep(5)
    assert tq.overflow == True
    assert tq.predicted_overflow == True
    assert tq.time_exceeded == True
    assert 4.95 < tq.time_this_step < 5.05
    assert 4.95 < tq.time_per_step < 5.05


def test_range():
    tq = TimeQuota(3, "s", name="range", verbose=False)

    # function
    assert list(tq.range(10)) == list(range(10))
    assert list(tq.range(1, 10, 2)) == list(range(1, 10, 2))
    assert list(tq.range(-2, -5, -1)) == list(range(-2, -5, -1))

    # time pre-exhausted
    tq.reset()
    time.sleep(5)
    for _ in tq.range(3):
        pass
    assert tq.overflow == True
    assert tq.predicted_overflow == False
    assert tq.time_exceeded == True

    # time not exhausted
    tq.reset()
    for _ in tq.range(3):
        time.sleep(0.5)
    assert tq.overflow == False
    assert tq.predicted_overflow == False
    assert tq.time_exceeded == False
    assert 0.5 < tq.time_this_step < 0.6
    assert 0.5 < tq.time_per_step < 0.6

    # time predicted exhausted
    tq.reset()
    for _ in tq.range(3):
        time.sleep(1.7)
    assert tq.overflow == False
    assert tq.predicted_overflow == True
    assert tq.time_exceeded == True
    assert 1.7 < tq.time_this_step < 1.8
    assert 1.7 < tq.time_per_step < 1.8

    # time exhausted
    tq.reset()
    for _ in tq.range(3):
        time.sleep(5)
    assert tq.overflow == True
    assert tq.predicted_overflow == True
    assert tq.time_exceeded == True
    assert 5 < tq.time_this_step < 5.1
    assert 5 < tq.time_per_step < 5.1


def test_str():
    tq = TimeQuota(3, "s", name="str-tq", color=False)

    for el in [
        "str-tq",
        "Time",
        "Time (s)",
        "-",
        "Quota",
        "Elapsed",
        "Remaining",
        "Per Step",
        "Exceeded",
        "00d 00h 00m 00s",
        "00d 00h 00m 03s",
        "3.0000s",
        "―",
        "False",
    ]:
        assert el in str(tq)
