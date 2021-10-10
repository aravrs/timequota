"""
**Manage the time of your python script.**

[[PyPI]](https://pypi.org/project/timequota/)
[[GitHub]](https://github.com/AravRS/timequota)
[[Demo Notebook]](https://github.com/AravRS/timequota/blob/main/demo.ipynb)
[[Changelog]](https://github.com/AravRS/timequota/blob/main/CHANGELOG.md)
"""

import sys
import time
from statistics import mean

from tabulate import tabulate
from colorama import Fore, Style

from collections import defaultdict
from typing import Any, List, Iterable, Iterator, Callable, Optional
from typeguard import typechecked


# provide compability with python<3.8
if sys.version_info[1] >= 8:
    from typing import Literal

    UnitType = Literal["s", "m", "h"]
    DisplayUnitType = Literal["s", "m", "h", "p"]
else:
    UnitType = str
    DisplayUnitType = str


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


@typechecked
class TimeQuota:
    def __init__(
        self,
        quota: float,
        unit: UnitType = "s",
        display_unit: DisplayUnitType = None,
        *,
        name: str = "tq",
        step_aggr_fn: Callable[[List[float]], float] = mean,
        timer_fn: Callable[[], float] = time.perf_counter,
        logger_fn: Optional[Callable[[str], None]] = print,
        precision: int = 4,
        color: bool = True,
        verbose: bool = True,
    ) -> None:
        """
        Args:
            quota (float): Maximum time limit.
            unit (Literal[s, m, h], optional): Unit of time of *quota* given, can be one of 's', 'm' or 'h' for seconds, minutes, or hours respectively . Defaults to 's'.
            display_unit (Literal[s, m, h, p], optional): Unit of time for logging messages, can be one of 's', 'm' or 'h' for seconds, minutes, or hours respectively; or 'p' for pretty format. Defaults to *unit*.
            name (str, optional): Custom name for quota timer. Defaults to 'tq'.
            step_aggr_fn (Callable[[list[float]], float], optional): Function to aggregate individual time steps, used for overflow prediction. Defaults to mean.
            timer_fn (Callable[[], float], optional): Function timer called before and after code execution to calculate the time taken. Defaults to time.perf_counter.
            logger_fn (Optional[Callable[[str], None]], optional): Custom info logger function. Defaults to print.
            precision (int, optional): Custom value precision for logging messages. Defaults to 4.
            color (bool, optional): Enable or disable color. Defaults to True.
            verbose (bool, optional): Enable or disable logging messages entirely. Defaults to True.
        """

        self.unit = unit.lower()
        self.display_unit = self.unit if display_unit is None else display_unit.lower()
        self.quota = float(quota) * _time_dict[self.unit]

        self.name = name
        self.step_aggr_fn = step_aggr_fn
        self.timer_fn = timer_fn
        self.logger_fn = logger_fn

        self.precision = precision
        self._color_dict = _color_dict if color else defaultdict(str)
        self.verbose = verbose

        self.reset()

    def reset(
        self,
    ) -> None:
        """
        Resets time quota to initial values.
        """

        self.time_elapsed: float = 0
        self.time_remaining: float = self.quota

        self.overflow: bool = False
        self.predicted_overflow: bool = False
        self.time_exceeded: bool = False

        self.time_steps: list[float] = []
        self.time_per_step: float = 0
        self.time_this_step: float = 0

        self.time_since: float = self.timer_fn()

    def _update_quota(
        self,
        track: bool = False,
    ) -> None:
        self.time_this_step = self.timer_fn() - self.time_since

        self.time_elapsed += self.time_this_step
        self.time_remaining -= self.time_this_step

        self.overflow = bool(self.time_remaining < 0)

        if track:
            self.time_steps.append(self.time_this_step)
            self.time_per_step = self.step_aggr_fn(self.time_steps)
            self.predicted_overflow = bool(self.time_per_step > self.time_remaining)

        self.time_exceeded = bool(self.overflow or self.predicted_overflow)

    def _get_display_string(
        self,
        seconds: float,
    ) -> str:

        if self.display_unit == "p":
            return self._get_pretty_string(seconds)

        if seconds == float("inf"):
            display_string = "inf"
        else:
            time_sign = "-" if seconds < 0 else ""
            seconds = abs(seconds)

            s = seconds / _time_dict["s"]
            m = seconds / _time_dict["m"]
            h = seconds / _time_dict["h"]

            if self.display_unit == "h" and h > 0:
                display_string = f"{time_sign}{h:.{self.precision}f}h"
            elif self.display_unit == "m" and m > 0:
                display_string = f"{time_sign}{m:.{self.precision}f}m"
            elif self.display_unit == "s" and s > 0:
                display_string = f"{time_sign}{s:.{self.precision}f}s"
            else:
                display_string = "―"

        return self._color_dict["c"] + display_string + self._color_dict["R"]

    def _get_pretty_string(
        self,
        seconds: float,
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

        return self._color_dict["c"] + pretty_string + self._color_dict["R"]

    def _get_time_exceeded_string(self):
        if self.overflow:
            return (
                f"{self._color_dict['g']}{self.name} {self._color_dict['r']}⚠ TIME EXCEEDED!{self._color_dict['R']} "
                f"Elapsed: {self._get_display_string(self.time_elapsed)}"
                f", Overflowed: {self._get_display_string(abs(self.time_remaining))}"
            )
        elif self.predicted_overflow:
            predicted_overflow_time = self.time_elapsed + self.time_per_step
            return (
                f"{self._color_dict['g']}{self.name} {self._color_dict['r']}⚠ TIME EXCEEDED! [Predicted]{self._color_dict['R']} "
                f"Estimated: {self._get_display_string(predicted_overflow_time)}"
                f", Overflow: {self._get_display_string(predicted_overflow_time - self.quota)}"
            )

    def _get_info_string(self, track=False):
        info_string = (
            f"{self._color_dict['g']}{self.name} » {self._color_dict['R']}"
            f"remaining: {self._get_display_string(self.time_remaining)}"
            f", elapsed: {self._get_display_string(self.time_elapsed)}"
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
        """
        Updates the quota considering the time taken from its creation to call.

        Args:
            verbose (bool, optional): Enable or disable logging messages. Defaults to True.

        Returns:
            bool: States if quota is exceeded.
        """

        self._update_quota()

        if (self.verbose and verbose) and self.logger_fn is not None:
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
        """
        Tracks, stores and updates the time taken every call, also used for quota overflow prediction. To be used in loops or repetitive calls.

        Args:
            verbose (bool, optional): Enable or disable logging messages. Defaults to True.
        Returns:
            bool: States if quota is exceeded.
        """

        self._update_quota(track=True)

        if (self.verbose and verbose) and self.logger_fn is not None:
            self.logger_fn(self._get_info_string(track=True))
            if self.time_exceeded:
                self.logger_fn(self._get_time_exceeded_string())

        self.time_since = self.timer_fn()
        return self.time_exceeded

    def iter(
        self,
        iterable: Iterable[Any],
        *,
        time_exceeded_fn: Optional[Callable] = None,
        time_exceeded_break: bool = True,
        verbose: bool = True,
    ) -> Iterator[Any]:
        """
        Time limited iterator of the iterable. When called, updates the quota and tracks time taken for each iteration, upon quota (predicted) exhaustion stops iteration (default).

        Iteration stops (default) under two conditions:
        (i) Exhaustion - Time taken by the iteration has already  exceeded the time quota and overflow occurs.
        (ii) Predicted exhaustion - The time taken by the next iteration (calculated by the *step_aggr_fn*) will exceed the time quota.

        Args:
            iterable (Iterable[Any]): Iterable to be iterated.
            time_exceeded_fn (Optional[Callable], optional): Function to be executed if time exceeds. Defaults to None.
            time_exceeded_break (bool, optional): To break out of the loop if time exceeds. Defaults to True.
            verbose (bool, optional): Enable or disable logging messages. Defaults to True.

        Yields:
            Iterator[Any]: Element in the iterable.
        """

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
        time_exceeded_fn: Optional[Callable] = None,
        time_exceeded_break: bool = True,
        verbose: bool = True,
        **kwargs: Any,
    ) -> Iterator[int]:
        """
        Time limited range. When called, updates the quota and tracks time taken for each iteration, upon quota (predicted) exhaustion stops iteration (default).

        Iteration stops (default) under two conditions:
            (i) Exhaustion - Time taken by the iteration has already  exceeded the time quota and overflow occurs.
            (ii) Predicted exhaustion - The time taken by the next iteration (calculated by the *step_aggr_fn*) will exceed the time quota.

        Args:
            time_exceeded_fn (Optional[Callable], optional): Function to be executed if time exceeds. Defaults to None.
            time_exceeded_break (bool, optional): To break out of the loop if time exceeds. Defaults to True.
            verbose (bool, optional): Enable or disable logging messages. Defaults to True.

        Yields:
            Iterator[int]: Sequence in the given number range.
        """

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
            f"{self._color_dict['g']}{self.name}{self._color_dict['R']}",
            f"{self._color_dict['y']}Time{self._color_dict['R']}",
            f"{self._color_dict['y']}Time ({self.display_unit}){self._color_dict['R']}",
        ]

        if self.overflow:
            time_exceeded_string = (
                self._color_dict["r"] + "True" + self._color_dict["R"]
            )
        elif self.predicted_overflow:
            time_exceeded_string = (
                self._color_dict["r"] + "Predicted" + self._color_dict["R"]
            )
        else:
            time_exceeded_string = (
                self._color_dict["c"] + "False" + self._color_dict["R"]
            )

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
        _quota = self.quota / _time_dict[self.unit]

        return (
            f"{self.__class__.__name__}"
            "("
            f"{_quota!r}, {self.unit!r}, {self.display_unit!r}, "
            f"name={self.name!r}, "
            f"step_aggr_fn={self.step_aggr_fn!r}, "
            f"timer_fn={self.timer_fn!r}, "
            f"logger_fn={self.logger_fn!r}, "
            f"precision={self.precision!r}, "
            f"color={any(self._color_dict.values())!r}, "
            f"verbose={self.verbose!r}"
            ")"
        )
