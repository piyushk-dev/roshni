"""Surya Saathi: a rooftop-solar copilot for households applying under PM Surya Ghar."""

import json
from importlib import resources


def load_data(name: str) -> dict:
    return json.loads(resources.files("surya.data").joinpath(name).read_text(encoding="utf-8"))
