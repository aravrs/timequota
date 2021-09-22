import time
from statistics import mean

from tabulate import tabulate
from colorama import Fore, Style

from collections import defaultdict
from typing import Any, Iterable, Callable, Union

_time_dict = {
    "s": 1,
    "m": 60,
    "h": 3600,
}

_color_dict = {
    "g": Fore.GREEN,
    "c": Fore.CYAN,
    "y": Fore.YELLOW,
    "r": Fore.RED,
    "R": Style.RESET_ALL,
}


class TimeQuota:
    def __init__(
        self,
        quota: Union[int, float],
        mode: str = "s",
        display_mode: str = None,
        *,
        name: str = "tq",
        step_aggr_fn: Callable[[list[float]], float] = mean,
        timer_fn: Callable[[], float] = time.perf_counter,
        logger_fn: Callable[[str], None] = print,
        precision: int = 4,
        color: bool = True,
        verbose: bool = True,
    ) -> None:

        self.mode = mode.lower()
        self.display_mode = self.mode if display_mode is None else display_mode.lower()
        self.quota = float(quota) * _time_dict[self.mode]

        self.name = name
        self.step_aggr_fn = step_aggr_fn
        self.timer_fn = timer_fn
        self.logger_fn = logger_fn

        self.precision = precision
        self.color = _color_dict if color else defaultdict(str)
        self.verbose = verbose

        self.reset()

    def reset(
        self,
    ) -> None:
        self.time_elapsed: float = 0
        self.time_remaining: float = self.quota

        self.overflow: bool = False
        self.predicted_overflow: bool = False
        self.time_exceeded: bool = False

        self.time_steps: list[float] = []
        self.time_per_step: float = 0
        self.time_this_step: float = 0

        self.time_since: Union[int, float] = self.timer_fn()

    def _update_quota(
        self,
        track: bool = False,
    ) -> None:
        self.time_this_step = self.timer_fn() - self.time_since

        self.time_elapsed += self.time_this_step
        self.time_remaining -= self.time_this_step

        self.overflow = self.time_remaining < 0

        if track:
            self.time_steps.append(self.time_this_step)
            self.time_per_step = self.step_aggr_fn(self.time_steps)
            self.predicted_overflow = self.time_per_step > self.time_remaining

        self.time_exceeded = self.overflow or self.predicted_overflow

    def _get_display_string(
        self,
        seconds: Union[int, float],
    ) -> str:

        if self.display_mode == "p":
            return self._get_pretty_string(seconds)

        if seconds == float("inf"):
            display_string = "inf"
        else:
            time_sign = "-" if seconds < 0 else ""
            seconds = abs(seconds)

            s = seconds / _time_dict["s"]
            m = seconds / _time_dict["m"]
            h = seconds / _time_dict["h"]

            if self.display_mode == "h" and h > 0:
                display_string = f"{time_sign}{h:.{self.precision}f}h"
            elif self.display_mode == "m" and m > 0:
                display_string = f"{time_sign}{m:.{self.precision}f}m"
            elif self.display_mode == "s" and s > 0:
                display_string = f"{time_sign}{s:.{self.precision}f}s"
            else:
                display_string = "―"

        return self.color["c"] + display_string + self.color["R"]

    def _get_pretty_string(
        self,
        seconds: Union[int, float],
        display: bool = False,
    ) -> str:

        if seconds == float("inf"):
            pretty_string = "inf"
        else:
            time_sign = "-" if seconds < 0 else ""
            seconds = abs(round(seconds))

            d = seconds // (3600 * 24)
            h = seconds // 3600 % 24
            m = seconds % 3600 // 60
            s = seconds % 3600 % 60

            if display or d > 0:
                pretty_string = f"{time_sign}{d:02d}d {h:02d}h {m:02d}m {s:02d}s"
            elif h > 0:
                pretty_string = f"{time_sign}{h:02d}h {m:02d}m {s:02d}s"
            elif m > 0:
                pretty_string = f"{time_sign}{m:02d}m {s:02d}s"
            elif s > 0:
                pretty_string = f"{time_sign}{s:02d}s"
            else:
                pretty_string = "―"

        return self.color["c"] + pretty_string + self.color["R"]

    def _get_time_exceeded_string(self):
        if self.overflow:
            return (
                f"{self.color['g']}{self.name} {self.color['r']}⚠ TIME EXCEEDED!{self.color['R']} "
                + f"Elapsed: {self._get_display_string(self.time_elapsed)}"
                + f", Overflowed: {self._get_display_string(abs(self.time_remaining))}"
            )
        elif self.predicted_overflow:
            predicted_overflow_time = self.time_elapsed + self.time_per_step
            return (
                f"{self.color['g']}{self.name} {self.color['r']}⚠ TIME EXCEEDED! [Predicted]{self.color['R']} "
                + f"Estimated: {self._get_display_string(predicted_overflow_time)}"
                + f", Overflow: {self._get_display_string(predicted_overflow_time - self.quota)}"
            )

    def _get_info_string(self, track=False):
        info_string = (
            f"{self.color['g']}{self.name} » {self.color['R']}"
            + f"remaining: {self._get_display_string(self.time_remaining)}"
            + f", elapsed: {self._get_display_string(self.time_elapsed)}"
        )

        if track:
            info_string += (
                f", this step: {self._get_display_string(self.time_this_step)}"
                + f", per step: {self._get_display_string(self.time_per_step)}"
            )

        return info_string

    def update(
        self,
        *,
        verbose: bool = True,
    ) -> bool:
        self._update_quota()

        if self.verbose and verbose:
            if self.time_exceeded:
                self.logger_fn(self._get_time_exceeded_string())
            else:
                self.logger_fn(self._get_info_string())

        self.time_since = self.timer_fn()
        return self.time_exceeded

    def track(
        self,
        *,
        verbose: bool = True,
    ) -> bool:
        self._update_quota(track=True)

        if self.verbose and verbose:
            self.logger_fn(self._get_info_string(track=True))
            if self.time_exceeded:
                self.logger_fn(self._get_time_exceeded_string())

        self.time_since = self.timer_fn()
        return self.time_exceeded

    def iter(
        self,
        iterable: Iterable[Any],
        *,
        time_exceeded_fn: Callable = None,
        time_exceeded_break: bool = True,
        verbose: bool = True,
    ) -> Iterable[Any]:
        if not self.update(verbose=verbose):
            for i in iterable:
                yield i

                if self.track(verbose=verbose):
                    if time_exceeded_fn is not None:
                        time_exceeded_fn()

                    if time_exceeded_break:
                        break

    def range(
        self,
        *args: Any,
        time_exceeded_fn: Callable = None,
        time_exceeded_break: bool = True,
        verbose: bool = True,
        **kwargs: Any,
    ) -> Iterable[int]:
        return self.iter(
            iterable=range(*args, **kwargs),
            time_exceeded_fn=time_exceeded_fn,
            time_exceeded_break=time_exceeded_break,
            verbose=verbose,
        )

    def __str__(
        self,
    ) -> str:
        headers = [
            f"{self.color['g']}{self.name}{self.color['R']}",
            f"{self.color['y']}Time{self.color['R']}",
            f"{self.color['y']}Time ({self.display_mode}){self.color['R']}",
        ]

        if self.overflow:
            time_exceeded_string = self.color["r"] + "True" + self.color["R"]
        elif self.predicted_overflow:
            time_exceeded_string = self.color["r"] + "Predicted" + self.color["R"]
        else:
            time_exceeded_string = self.color["c"] + "False" + self.color["R"]

        table = [
            [
                "Time Quota",
                self._get_pretty_string(self.quota, display=True),
                self._get_display_string(self.quota),
            ],
            [
                "Time Elapsed",
                self._get_pretty_string(self.time_elapsed, display=True),
                self._get_display_string(self.time_elapsed),
            ],
            [
                "Time Remaining",
                self._get_pretty_string(self.time_remaining, display=True),
                self._get_display_string(self.time_remaining),
            ],
            [
                "Time Per Step",
                self._get_pretty_string(self.time_per_step, display=True),
                self._get_display_string(self.time_per_step),
            ],
            [
                "Time Exceeded",
                time_exceeded_string,
                time_exceeded_string,
            ],
        ]

        return tabulate(
            table,
            headers,
            colalign=("left", "right", "right"),
            tablefmt="simple",
        )

    def __repr__(
        self,
    ) -> str:
        _quota = self.quota / _time_dict[self.mode]

        return (
            f"{self.__class__.__name__}"
            + "("
            + f"{_quota!r}, {self.mode!r}, {self.display_mode!r}, {self.name!r}"
            + ")"
        )
