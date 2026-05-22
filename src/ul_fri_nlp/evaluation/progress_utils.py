import time


class Progress:
    def __init__(self, total, label="progress", every=1):
        self.total = max(0, int(total))
        self.label = label
        self.every = max(1, int(every))
        self.start = time.time()

    def log(self, current, message=""):
        current = int(current)
        if current != self.total and current % self.every:
            return
        elapsed = time.time() - self.start
        rate = current / elapsed if elapsed > 0 else 0.0
        pct = (current / self.total * 100.0) if self.total else 100.0
        suffix = f" | {message}" if message else ""
        print(
            f"[{self.label}] {current}/{self.total} ({pct:5.1f}%) "
            f"| {rate:.2f} items/s{suffix}",
            flush=True,
        )
