"""Shared fixtures for Elpriset Just Nu tests."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest

from custom_components.elprisetjustnu.const import CONF_REGION, CONF_UNIT

# --- Constants ---

CET = timezone(timedelta(hours=1))

MOCK_CONFIG_DATA = {
    CONF_REGION: "SE3",
    CONF_UNIT: "öre/kWh",
}


# --- Helpers ---


def _make_slot(date_str: str, hour: int, minute: int, sek_price: float) -> dict:
    """Create a single 15-minute API price slot."""
    start = datetime.fromisoformat(f"{date_str}T{hour:02d}:{minute:02d}:00+01:00")
    end = start + timedelta(minutes=15)
    return {
        "SEK_per_kWh": sek_price,
        "EUR_per_kWh": round(sek_price / 11.5, 6),
        "EXR": 11.5,
        "time_start": start.isoformat(),
        "time_end": end.isoformat(),
    }


def make_day_data(date_str: str = "2026-03-31", base_price: float = 1.0, slots: int = 96) -> list[dict]:
    """Generate a full day of 15-minute price slots with a realistic curve."""
    data = []
    for i in range(slots):
        hour = i // 4
        minute = (i % 4) * 15
        # Cheap at night, peak around 8:00 and 18:00
        if 7 <= hour <= 9 or 17 <= hour <= 19:
            factor = 1.8
        elif 0 <= hour <= 5:
            factor = 0.4
        else:
            factor = 1.0
        price = round(base_price * factor + (i % 7) * 0.01, 4)
        data.append(_make_slot(date_str, hour, minute, price))
    return data


SAMPLE_TODAY = make_day_data("2026-03-31", base_price=1.0)
SAMPLE_TOMORROW = make_day_data("2026-04-01", base_price=1.2)


# --- Fixtures ---


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests.

    This fixture is provided by pytest-homeassistant-custom-component
    and makes HA discover custom_components/ during tests.
    """
    yield


@pytest.fixture
def mock_api_today():
    """Return sample today data."""
    return SAMPLE_TODAY.copy()


@pytest.fixture
def mock_api_tomorrow():
    """Return sample tomorrow data."""
    return SAMPLE_TOMORROW.copy()
