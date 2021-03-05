import time
import numpy as np


class TimeQuota:
    def __init__(self, quota):
        self.quota = quota

        self.time_elapsed = 0
        self.time_remaining = self.quota

        self.time_since = time.time()

        self.time_steps = []
        self.time_per_step = 0

    def update(self, verbose=True):

        time_used = time.time() - self.time_since

        self.time_elapsed += time_used
        self.time_remaining -= time_used
        self.time_since = time.time()

        if verbose:
            print(
                f"> time remaining: {self.time_remaining:.4f}",
                f"time elapsed: {self.time_elapsed:.4f}",
                sep=" | ",
            )

    def track(self, verbose=True):

        time_used = time.time() - self.time_since

        self.time_steps.append(time_used)
        self.time_per_step = np.mean(self.time_steps)

        self.time_elapsed += time_used
        self.time_remaining -= time_used
        self.time_since = time.time()

        if verbose:
            print(
                f"> time remaining: {self.time_remaining:.4f}",
                f"time elapsed: {self.time_elapsed:.4f}",
                f"time this step: {time_used:.4f}",
                f"time per step: {self.time_per_step:.4f}",
                sep=" | ",
            )

        if self.time_per_step > self.time_remaining:
            print(f"\n> TIME EXCEEDED: {self.time_elapsed + self.time_per_step:.4f}")
            return True

        return False