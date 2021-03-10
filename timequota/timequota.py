import time
import numpy as np
from prettytable import PrettyTable


class TimeQuota:
    def __init__(self, quota, name="tq", verbose=True):
        self.quota = quota

        self.time_elapsed = 0
        self.time_remaining = self.quota
        self.time_exceeded = False

        self.time_since = time.time()

        self.time_steps = []
        self.time_per_step = 0

        self.name = name
        self.verbose = verbose

    def update(self, verbose=True):

        time_used = time.time() - self.time_since

        self.time_elapsed += time_used
        self.time_remaining -= time_used
        self.time_since = time.time()

        if self.time_exceeded or self.time_remaining < 0:
            print(f"\n{self.name} > TIME EXCEEDED!")
            self.time_exceeded = True

        if self.verbose and verbose:
            print(
                f"{self.name} > " + f"time remaining: {self.time_remaining:.4f}",
                f"time elapsed: {self.time_elapsed:.4f}",
                sep=" | ",
            )

        return self.time_exceeded

    def track(self, verbose=True):

        if not (self.time_exceeded or self.time_remaining < 0):
            time_used = time.time() - self.time_since

            self.time_steps.append(time_used)
            self.time_per_step = np.mean(self.time_steps)

            self.time_elapsed += time_used
            self.time_remaining -= time_used
            self.time_since = time.time()

            if self.verbose and verbose:
                print(
                    f"{self.name} > " + f"time remaining: {self.time_remaining:.4f}",
                    f"time elapsed: {self.time_elapsed:.4f}",
                    f"time this step: {time_used:.4f}",
                    f"time per step: {self.time_per_step:.4f}",
                    sep=" | ",
                )

        if self.time_exceeded or (self.time_per_step > self.time_remaining):
            print(
                f"\n{self.name} > TIME EXCEEDED!",
                f"Estimated: {self.time_elapsed + self.time_per_step:.4f}",
            )
            self.time_exceeded = True

        return self.time_exceeded

    def __str__(self):

        pt = PrettyTable(border=True, header=True, padding_width=2)
        pt.field_names = [self.name, f"Time (s)"]

        pt.add_rows(
            [
                ["Time Quota", f"{self.quota:.4f}"],
                ["Time Elapsed", f"{self.time_elapsed:.4f}"],
                ["Time Remaining", f"{self.time_remaining:.4f}"],
                ["Time Per Step", f"{self.time_per_step:.4f}"],
                ["Time Exceeded", self.time_exceeded],
            ]
        )

        pt.align[self.name] = "l"
        pt.align[f"Time (s)"] = "r"

        return pt.get_string()

    def __repr__(self):

        return (
            f"{self.__class__.__name__}"
            + "("
            + f"{self.quota!r}, {self.name!r}, {self.verbose!r}"
            + ")"
        )
