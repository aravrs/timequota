import time
from statistics import mean
from prettytable import PrettyTable


class TimeQuota:
    def __init__(
        self,
        quota,
        mode="s",
        display_mode=None,
        name="tq",
        verbose=True,
    ):

        self.mode = mode.lower()
        self.display_mode = self.mode if display_mode is None else display_mode

        self.quota = 0
        if self.mode == "s":
            self.quota = quota
        elif self.mode == "m":
            self.quota = quota * 60
        elif self.mode == "h":
            self.quota = quota * 3600

        self.name = name
        self.verbose = verbose

        self.reset()

    def _update_quota(
        self,
        track=False,
    ):
        self.time_this_step = time.time() - self.time_since

        self.time_elapsed += self.time_this_step
        self.time_remaining -= self.time_this_step

        if track:
            self.time_steps.append(self.time_this_step)
            self.time_per_step = mean(self.time_steps)

        self.time_exceeded = (self.time_remaining < 0) or (
            self.time_per_step > self.time_remaining
        )

    def _get_display_string(
        self,
        seconds,
    ):
        s = seconds
        m = seconds / 60
        h = seconds / 3600

        if self.display_mode == "p":
            return self._get_pretty_string(seconds)
        elif self.display_mode == "h" and h > 0:
            return f"{h:.4f} hrs"
        elif self.display_mode == "m" and m > 0:
            return f"{m:.4f} mins"
        elif self.display_mode == "s" and s > 0:
            return f"{s:.4f} secs"

        return "-"

    def _get_pretty_string(
        self,
        seconds,
    ):
        seconds = round(seconds)

        d = seconds // (3600 * 24)
        h = seconds // 3600 % 24
        m = seconds % 3600 // 60
        s = seconds % 3600 % 60

        if d > 0:
            return f"{d:02d}d {h:02d}h {m:02d}m {s:02d}s"
        elif h > 0:
            return f"{h:02d}h {m:02d}m {s:02d}s"
        elif m > 0:
            return f"{m:02d}m {s:02d}s"
        elif s > 0:
            return f"{s:02d}s"

        return "-"

    def update(
        self,
        verbose=True,
    ):
        self._update_quota()

        if self.verbose and verbose:

            if self.time_exceeded:
                print(
                    f"\n{self.name} > TIME EXCEEDED!",
                    f"Elapsed: {self._get_display_string(self.time_elapsed)}, Overflow: {self._get_display_string(abs(self.time_remaining))}",
                )
            else:
                print(
                    f"{self.name} > "
                    + f"time remaining: {self._get_display_string(self.time_remaining)}",
                    f"time elapsed: {self._get_display_string(self.time_elapsed)}",
                    sep=" | ",
                )

        self.time_since = time.time()
        return self.time_exceeded

    def track(
        self,
        verbose=True,
    ):
        self._update_quota(track=True)

        if self.verbose and verbose:

            print(
                f"{self.name} > "
                + f"time remaining: {self._get_display_string(self.time_remaining)}",
                f"time elapsed: {self._get_display_string(self.time_elapsed)}",
                f"time this step: {self._get_display_string(self.time_this_step)}",
                f"time per step: {self._get_display_string(self.time_per_step)}",
                sep=" | ",
            )

            if self.time_exceeded:
                print(
                    f"\n{self.name} > TIME EXCEEDED!",
                    f"Estimated: {self._get_display_string(self.time_elapsed + self.time_per_step)}",
                )

        self.time_since = time.time()
        return self.time_exceeded

    def range(
        self,
        *args,
        verbose=True,
        **kwargs,
    ):
        self.update(verbose=verbose)
        print()

        i = iter(range(*args, **kwargs))

        while True:
            try:
                yield next(i)
            except StopIteration:
                break

            if self.track(verbose=verbose):
                break

    def reset(
        self,
    ):
        self.time_elapsed = 0
        self.time_remaining = self.quota
        self.time_exceeded = False

        self.time_steps = []
        self.time_per_step = 0
        self.time_this_step = 0

        self.time_since = time.time()

    def __str__(
        self,
    ):

        pt = PrettyTable(
            border=True,
            header=True,
            padding_width=2,
        )
        pt.field_names = [
            self.name,
            "Time",
            f"Time ({self.display_mode})",
        ]

        pt.add_rows(
            [
                [
                    "Time Quota",
                    self._get_pretty_string(self.quota),
                    self._get_display_string(self.quota),
                ],
                [
                    "Time Elapsed",
                    self._get_pretty_string(self.time_elapsed),
                    self._get_display_string(self.time_elapsed),
                ],
                [
                    "Time Remaining",
                    self._get_pretty_string(self.time_remaining),
                    self._get_display_string(self.time_remaining),
                ],
                [
                    "Time Per Step",
                    self._get_pretty_string(self.time_per_step),
                    self._get_display_string(self.time_per_step),
                ],
                [
                    "Time Exceeded",
                    self.time_exceeded,
                    self.time_exceeded,
                ],
            ]
        )

        pt.align[self.name] = "l"
        pt.align[f"Time ({self.display_mode})"] = "r"
        pt.align["Time"] = "r"

        return pt.get_string()

    def __repr__(
        self,
    ):

        return (
            f"{self.__class__.__name__}"
            + "("
            + f"{self.quota!r}, {self.mode!r}, {self.display_mode!r}, {self.name!r}, {self.verbose!r}"
            + ")"
        )
