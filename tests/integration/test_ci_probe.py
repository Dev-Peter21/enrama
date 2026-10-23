"""Temporary CI failure probe; never merge this branch."""

import os


def test_ci_failure_probe() -> None:
    assert False, "Intentional F03 CI failure propagation probe"
