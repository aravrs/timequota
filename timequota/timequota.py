import time
from statistics import mean

from tabulate import tabulate
from colorama import Fore, Style

from collections import defaultdict
from typing import Any, Optional, Iterable, Callable, Union


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
        mode: Optional[str] = "s",
        display_mode: Optional[str] = None,
        *,
        name: Optional[str] = "tq",
        step_aggr_fn: Optional[Callable] = mean,
        timer_fn: Optional[str] = "perf_counter",
        logger_fn: Optional[Callable] = print,
        precision: Optional[int] = 4,
        color: Optional[bool] = True,
        verbose: Optional[bool] = True,
    ) -> None:
        self.mode = mode.lower()
        self.display_mode = self.mode if display_mode is None else display_mode.lower()

        self.quota = 0
        if self.mode == "s":
            self.quota = quota
        elif self.mode == "m":
            self.quota = quota * 60
        elif self.mode == "h":
            self.quota = quota * 3600

        self.name = name
        self.step_aggr_fn = step_aggr_fn
        self.timer_fn = getattr(time, timer_fn)
        self.logger_fn = logger_fn
        self.precision = precision
        self.color = _color_dict if color else defaultdict(str)
        self.verbose = verbose

        self.reset()

    def _update_quota(
        self,
        track: Optional[bool] = False,
    ) -> None:
        self.time_this_step = self.timer_fn() - self.time_since

        self.time_elapsed += self.time_this_step
        self.time_remaining -= self.time_this_step

        if track:
            self.time_steps.append(self.time_this_step)
            self.time_per_step = self.step_aggr_fn(self.time_steps)

        self.time_exceeded = (self.time_remaining < 0) or (
            self.time_per_step > self.time_remaining
        )

    def _get_display_string(
        self,
        seconds: Union[int, float],
    ) -> str:
        if self.display_mode == "p":
            return self._get_pretty_string(seconds)

        time_sign = "-" if seconds < 0 else ""
        seconds = abs(seconds)

        s = seconds
        m = seconds / 60
        h = seconds / 3600

        if self.display_mode == "h" and h > 0:
            return (
                f"{self.color['c']}{time_sign}{h:.{self.precision}f}h{self.color['R']}"
            )
        elif self.display_mode == "m" and m > 0:
            return (
                f"{self.color['c']}{time_sign}{m:.{self.precision}f}m{self.color['R']}"
            )
        elif self.display_mode == "s" and s > 0:
            return (
                f"{self.color['c']}{time_sign}{s:.{self.precision}f}s{self.color['R']}"
            )

        return f"{self.color['c']}―{self.color['R']}"

    def _get_pretty_string(
        self,
        seconds: Union[int, float],
        display: Optional[bool] = False,
    ) -> str:
        time_sign = "-" if seconds < 0 else ""
        seconds = abs(round(seconds))

        d = seconds // (3600 * 24)
        h = seconds // 3600 % 24
        m = seconds % 3600 // 60
        s = seconds % 3600 % 60

        if display or d > 0:
            return f"{self.color['c']}{time_sign}{d:02d}d {h:02d}h {m:02d}m {s:02d}s{self.color['R']}"
        elif h > 0:
            return f"{self.color['c']}{time_sign}{h:02d}h {m:02d}m {s:02d}s{self.color['R']}"
        elif m > 0:
            return f"{self.color['c']}{time_sign}{m:02d}m {s:02d}s{self.color['R']}"
        elif s > 0:
            return f"{self.color['c']}{time_sign}{s:02d}s{self.color['R']}"

        return f"{self.color['c']}―{self.color['R']}"

    def update(
        self,
        *,
        verbose: Optional[bool] = True,
    ) -> bool:
        self._update_quota()

        if self.verbose and verbose:

            if self.time_exceeded:
                print(
                    f"\n{self.color['g']}{self.name}{self.color['R']} {self.color['r']}⚠ TIME EXCEEDED!{self.color['R']}",
                    f"Elapsed: {self._get_display_string(self.time_elapsed)}, Overflow: {self._get_display_string(abs(self.time_remaining))}",
                )
            else:
                print(
                    f"{self.color['g']}{self.name} » {self.color['R']}"
                    + f"remaining: {self._get_display_string(self.time_remaining)}",
                    f"elapsed: {self._get_display_string(self.time_elapsed)}",
                    sep=", ",
                )

        self.time_since = self.timer_fn()
        return self.time_exceeded

    def track(
        self,
        *,
        verbose: Optional[bool] = True,
    ) -> bool:
        self._update_quota(track=True)

        if self.verbose and verbose:

            print(
                f"{self.color['g']}{self.name} » {self.color['R']}"
                + f"remaining: {self._get_display_string(self.time_remaining)}",
                f"elapsed: {self._get_display_string(self.time_elapsed)}",
                f"this step: {self._get_display_string(self.time_this_step)}",
                f"per step: {self._get_display_string(self.time_per_step)}",
                sep=", ",
            )

            if self.time_exceeded:
                print(
                    f"\n{self.color['g']}{self.name}{self.color['R']} {self.color['r']}⚠ TIME EXCEEDED!{self.color['R']}",
                    f"Estimated: {self._get_display_string(self.time_elapsed + self.time_per_step)}",
                )

        self.time_since = self.timer_fn()
        return self.time_exceeded

    def range(
        self,
        *args: Any,
        time_exceeded_fn: Optional[Callable] = None,
        time_exceeded_break: Optional[bool] = True,
        verbose: Optional[bool] = True,
        **kwargs: Any,
    ) -> Iterable[int]:
        if not self.update(verbose=verbose):
            for i in range(*args, **kwargs):
                yield i

                if self.track(verbose=verbose):
                    if time_exceeded_fn is not None:
                        time_exceeded_fn()

                    if time_exceeded_break:
                        break

    def iter(
        self,
        iterable: Iterable[Any],
        *,
        time_exceeded_fn: Optional[Callable] = None,
        time_exceeded_break: Optional[bool] = True,
        verbose: Optional[bool] = True,
    ) -> Iterable[Any]:
        if not self.update(verbose=verbose):
            for i in iterable:
                yield i

                if self.track(verbose=verbose):
                    if time_exceeded_fn is not None:
                        time_exceeded_fn()

                    if time_exceeded_break:
                        break

    def reset(
        self,
    ) -> None:
        self.time_elapsed = 0
        self.time_remaining = self.quota
        self.time_exceeded = False

        self.time_steps = []
        self.time_per_step = 0
        self.time_this_step = 0

        self.time_since = self.timer_fn()

    def __str__(
        self,
    ) -> str:
        headers = [
            f"{self.color['g']}{self.name}{self.color['R']}",
            f"{self.color['y']}Time{self.color['R']}",
            f"{self.color['y']}Time ({self.display_mode}){self.color['R']}",
        ]

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
                f"{self.color['r']}True{self.color['R']}"
                if self.time_exceeded
                else f"{self.color['c']}False{self.color['R']}",
                f"{self.color['r']}True{self.color['R']}"
                if self.time_exceeded
                else f"{self.color['c']}False{self.color['R']}",
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
        _quota = self.quota
        if self.mode == "m":
            _quota /= 60
        elif self.mode == "h":
            _quota /= 3600

        return (
            f"{self.__class__.__name__}"
            + "("
            + f"{_quota!r}, {self.mode!r}, {self.display_mode!r}, {self.name!r}"
            + ")"
        )
