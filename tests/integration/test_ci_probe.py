"""Temporary CI cancellation probe; never merge this branch."""

import os
import time


def test_ci_failure_probe() -> None:
    time.sleep(120)
    assert False, "Intentional F03 cancellation window"
