import time
from statistics import mean

from tabulate import tabulate
from colorama import Fore, Style
from typing import Any, Optional, Iterable, Callable, Union


class TimeQuota:
    def __init__(
        self,
        quota: Union[int, float],
        mode: Optional[str] = "s",
        display_mode: Optional[str] = None,
        *,
        name: Optional[str] = "tq",
        step_aggr_fn: Optional[Callable] = mean,
        precision: Optional[int] = 4,
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
        self.precision = precision
        self.verbose = verbose

        self.reset()

    def _update_quota(
        self,
        track: Optional[bool] = False,
    ) -> None:
        self.time_this_step = time.time() - self.time_since

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
            return f"{Fore.CYAN}{time_sign}{h:.{self.precision}f}h{Style.RESET_ALL}"
        elif self.display_mode == "m" and m > 0:
            return f"{Fore.CYAN}{time_sign}{m:.{self.precision}f}m{Style.RESET_ALL}"
        elif self.display_mode == "s" and s > 0:
            return f"{Fore.CYAN}{time_sign}{s:.{self.precision}f}s{Style.RESET_ALL}"

        return "-"

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
            return f"{Fore.CYAN}{time_sign}{d:02d}d {h:02d}h {m:02d}m {s:02d}s{Style.RESET_ALL}"
        elif h > 0:
            return f"{Fore.CYAN}{time_sign}{h:02d}h {m:02d}m {s:02d}s{Style.RESET_ALL}"
        elif m > 0:
            return f"{Fore.CYAN}{time_sign}{m:02d}m {s:02d}s{Style.RESET_ALL}"
        elif s > 0:
            return f"{Fore.CYAN}{time_sign}{s:02d}s{Style.RESET_ALL}"

        return "-"

    def update(
        self,
        *,
        verbose: Optional[bool] = True,
    ) -> bool:
        self._update_quota()

        if self.verbose and verbose:

            if self.time_exceeded:
                print(
                    f"\n{Fore.GREEN}{self.name}{Style.RESET_ALL} {Fore.RED}⚠ TIME EXCEEDED!{Style.RESET_ALL}",
                    f"Elapsed: {self._get_display_string(self.time_elapsed)}, Overflow: {self._get_display_string(abs(self.time_remaining))}",
                )
            else:
                print(
                    f"{Fore.GREEN}{self.name} » {Style.RESET_ALL}"
                    + f"remaining: {self._get_display_string(self.time_remaining)}",
                    f"elapsed: {self._get_display_string(self.time_elapsed)}",
                    sep=", ",
                )

        self.time_since = time.time()
        return self.time_exceeded

    def track(
        self,
        *,
        verbose: Optional[bool] = True,
    ) -> bool:
        self._update_quota(track=True)

        if self.verbose and verbose:

            print(
                f"{Fore.GREEN}{self.name} » {Style.RESET_ALL}"
                + f"remaining: {self._get_display_string(self.time_remaining)}",
                f"elapsed: {self._get_display_string(self.time_elapsed)}",
                f"this step: {self._get_display_string(self.time_this_step)}",
                f"per step: {self._get_display_string(self.time_per_step)}",
                sep=", ",
            )

            if self.time_exceeded:
                print(
                    f"\n{Fore.GREEN}{self.name}{Style.RESET_ALL} {Fore.RED}⚠ TIME EXCEEDED!{Style.RESET_ALL}",
                    f"Estimated: {self._get_display_string(self.time_elapsed + self.time_per_step)}",
                )

        self.time_since = time.time()
        return self.time_exceeded

    def range(
        self,
        *args: Any,
        time_exceeded_fn: Optional[Callable] = None,
        time_exceeded_break: Optional[bool] = True,
        verbose: Optional[bool] = True,
        **kwargs: Any,
    ) -> Iterable[int]:
        i = iter(range(*args, **kwargs))

        if not self.update(verbose=verbose):
            while True:
                try:
                    yield next(i)
                except StopIteration:
                    break

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
        i = iter(iterable)

        if not self.update(verbose=verbose):
            while True:
                try:
                    yield next(i)
                except StopIteration:
                    break

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

        self.time_since = time.time()

    def __str__(
        self,
    ) -> str:

        headers = [
            f"{Fore.GREEN}{self.name}{Style.RESET_ALL}",
            f"{Fore.YELLOW}Time{Style.RESET_ALL}",
            f"{Fore.YELLOW}Time ({self.display_mode}){Style.RESET_ALL}",
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
                f"{Fore.RED}True{Style.RESET_ALL}"
                if self.time_exceeded
                else f"{Fore.CYAN}False{Style.RESET_ALL}",
                f"{Fore.RED}True{Style.RESET_ALL}"
                if self.time_exceeded
                else f"{Fore.CYAN}False{Style.RESET_ALL}",
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
