import json
from pathlib import Path

import pytest

from surya.solar import solar_yield

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def delhi_sources() -> dict:
    return json.loads((FIXTURES / "delhi_sources.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def delhi_yield(delhi_sources):
    return solar_yield(delhi_sources)


# Jan..Dec units for three kinds of Delhi homes
HEAVY_AC = [380, 350, 420, 560, 720, 780, 690, 610, 560, 470, 390, 400]
MODERATE = [300, 280, 320, 420, 520, 560, 500, 450, 420, 360, 300, 310]
LOW = [150, 140, 160, 190, 240, 260, 230, 210, 190, 170, 150, 150]


def months(units: list[float]) -> dict[int, float]:
    return dict(enumerate(units, start=1))


@pytest.fixture(autouse=True)
def no_network_classifier(monkeypatch):
    """Photos route as bills unless a test says otherwise; never call Bedrock from tests."""
    from surya import performance

    monkeypatch.setattr(performance, "classify", lambda data, media_type, client=None: "electricity_bill")


@pytest.fixture(autouse=True)
def no_real_aws(monkeypatch):
    """Tests run offline: reaching for a real AWS client fails loudly instead of using local credentials."""
    import boto3

    def refuse(*args, **kwargs):
        raise RuntimeError(f"a test tried to reach AWS ({args[0] if args else kwargs.get('service_name')}); patch it")

    monkeypatch.setattr(boto3, "client", refuse)
    monkeypatch.setattr(boto3, "resource", refuse)
