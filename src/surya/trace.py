"""A short record of which service did each step of an answer, and how long it took.

The website shows it under a result, so the work AWS does is visible: the bill read on Bedrock, the
sunlight from DynamoDB's cache (or from PVGIS and NASA POWER the first time), the sums in Lambda.
One Lambda invocation handles one request at a time, so a module-level list is enough.
"""

from __future__ import annotations

import time
from contextlib import contextmanager

_steps: list[dict] = []


def start() -> None:
    _steps.clear()


@contextmanager
def step(service: str, what: str, **extra):
    began = time.perf_counter()
    try:
        yield extra
    finally:
        _steps.append({"service": service, "what": what, "ms": round((time.perf_counter() - began) * 1000), **extra})


def steps() -> list[dict]:
    return list(_steps)
