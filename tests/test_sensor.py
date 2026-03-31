"""Tests for the Elpriset Just Nu sensor platform."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from custom_components.elprisetjustnu.sensor import (
    ElprisSensor,
    SENSOR_TYPES,
    _convert,
    _get_price_level,
    _find_block,
)

from .conftest import SAMPLE_TODAY, SAMPLE_TOMORROW, CET


# ---------------------------------------------------------------------------
# Unit conversion tests
# ---------------------------------------------------------------------------


def test_convert_ore():
    """Test SEK to öre conversion."""
    assert _convert(1.5, "öre/kWh") == 150.0
    assert _convert(0.123, "öre/kWh") == 12.3


def test_convert_sek():
    """Test SEK pass-through."""
    assert _convert(1.5, "SEK/kWh") == 1.5
    assert _convert(0.1234, "SEK/kWh") == 0.1234


def test_convert_zero():
    """Test zero price conversion."""
    assert _convert(0.0, "öre/kWh") == 0.0
    assert _convert(0.0, "SEK/kWh") == 0.0


# ---------------------------------------------------------------------------
# Price level classification tests
# ---------------------------------------------------------------------------


def test_price_level_cheap():
    assert _get_price_level(10, 10, 100) == "cheap"
    assert _get_price_level(30, 10, 100) == "cheap"


def test_price_level_expensive():
    assert _get_price_level(90, 10, 100) == "expensive"
    assert _get_price_level(100, 10, 100) == "expensive"


def test_price_level_normal():
    assert _get_price_level(50, 10, 100) == "normal"


def test_price_level_flat():
    """All prices the same should be 'normal'."""
    assert _get_price_level(50, 50, 50) == "normal"


# ---------------------------------------------------------------------------
# _find_block tests
# ---------------------------------------------------------------------------


def test_find_block_match():
    """Find the block that contains 10:07 CET."""
    now = datetime(2026, 3, 31, 10, 7, tzinfo=CET)
    block = _find_block(
        SAMPLE_TODAY,
        lambda s, e: s <= now < e,
    )
    assert block is not None
    assert "10:00:00" in block["time_start"]


def test_find_block_no_match():
    """No block matches a time outside the data range."""
    far_future = datetime(2099, 1, 1, 0, 0, tzinfo=CET)
    block = _find_block(
        SAMPLE_TODAY,
        lambda s, e: s <= far_future < e,
    )
    assert block is None


def test_find_block_empty_list():
    assert _find_block([], lambda s, e: True) is None


# ---------------------------------------------------------------------------
# Sensor entity tests
# ---------------------------------------------------------------------------


def _make_coordinator_mock(today=None, tomorrow=None):
    """Create a mock coordinator with data."""
    coordinator = MagicMock()
    coordinator.data = {
        "today": today or [],
        "tomorrow": tomorrow or [],
    }
    return coordinator


def _make_sensor(key: str, unit: str = "öre/kWh", today=None, tomorrow=None):
    """Create a sensor with a mock coordinator for testing."""
    coord = _make_coordinator_mock(today, tomorrow)
    desc = next(d for d in SENSOR_TYPES if d.key == key)

    sensor = ElprisSensor.__new__(ElprisSensor)
    sensor.coordinator = coord
    sensor.entity_description = desc
    sensor.region = "SE3"
    sensor._unit = unit
    sensor._attr_unique_id = f"test_{key}"
    sensor._attr_has_entity_name = True
    sensor._attr_native_unit_of_measurement = unit
    return sensor


class TestCurrentPriceSensor:
    """Tests for the current_price sensor."""

    def test_returns_value_for_matching_slot(self):
        now = datetime(2026, 3, 31, 10, 7, tzinfo=CET)
        with patch(
            "custom_components.elprisetjustnu.sensor.dt_util"
        ) as mock_dt:
            mock_dt.now.return_value = now

            sensor = _make_sensor("current_price", today=SAMPLE_TODAY)
            value = sensor.native_value

        assert value is not None
        assert isinstance(value, float)
        assert value > 0

    def test_returns_none_when_no_data(self):
        sensor = _make_sensor("current_price", today=[])
        assert sensor.native_value is None

    def test_returns_none_when_no_matching_slot(self):
        far_future = datetime(2099, 1, 1, 0, 0, tzinfo=CET)
        with patch(
            "custom_components.elprisetjustnu.sensor.dt_util"
        ) as mock_dt:
            mock_dt.now.return_value = far_future

            sensor = _make_sensor("current_price", today=SAMPLE_TODAY)
            assert sensor.native_value is None

    def test_sek_unit(self):
        now = datetime(2026, 3, 31, 10, 7, tzinfo=CET)
        with patch(
            "custom_components.elprisetjustnu.sensor.dt_util"
        ) as mock_dt:
            mock_dt.now.return_value = now

            sensor = _make_sensor("current_price", unit="SEK/kWh", today=SAMPLE_TODAY)
            value = sensor.native_value

        assert value is not None
        # SEK values should be around 0.4-1.8 range, not 40-180
        assert value < 10


class TestHighLowAverageSensors:
    """Tests for aggregate sensors."""

    def test_highest_price_today(self):
        sensor = _make_sensor("highest_price_today", today=SAMPLE_TODAY)
        value = sensor.native_value
        assert value is not None
        prices = [_convert(b["SEK_per_kWh"], "öre/kWh") for b in SAMPLE_TODAY]
        assert value == round(max(prices), 4)

    def test_lowest_price_today(self):
        sensor = _make_sensor("lowest_price_today", today=SAMPLE_TODAY)
        value = sensor.native_value
        assert value is not None
        prices = [_convert(b["SEK_per_kWh"], "öre/kWh") for b in SAMPLE_TODAY]
        assert value == round(min(prices), 4)

    def test_average_price_today(self):
        sensor = _make_sensor("average_price_today", today=SAMPLE_TODAY)
        value = sensor.native_value
        assert value is not None
        prices = [_convert(b["SEK_per_kWh"], "öre/kWh") for b in SAMPLE_TODAY]
        assert value == round(sum(prices) / len(prices), 4)

    def test_returns_none_when_empty(self):
        sensor = _make_sensor("highest_price_today", today=[])
        assert sensor.native_value is None


class TestNextPriceSensor:
    """Tests for the next_price sensor."""

    def test_returns_next_slot(self):
        now = datetime(2026, 3, 31, 10, 7, tzinfo=CET)
        with patch(
            "custom_components.elprisetjustnu.sensor.dt_util"
        ) as mock_dt:
            mock_dt.now.return_value = now

            sensor = _make_sensor("next_price", today=SAMPLE_TODAY)
            value = sensor.native_value

        assert value is not None

    def test_returns_none_at_end_of_day(self):
        late = datetime(2026, 3, 31, 23, 55, tzinfo=CET)
        with patch(
            "custom_components.elprisetjustnu.sensor.dt_util"
        ) as mock_dt:
            mock_dt.now.return_value = late

            sensor = _make_sensor("next_price", today=SAMPLE_TODAY)
            value = sensor.native_value

        # The last slot ends at 00:00, so there should be no next slot
        assert value is None


class TestTomorrowSensors:
    """Tests for tomorrow price sensors."""

    def test_highest_tomorrow(self):
        sensor = _make_sensor(
            "highest_price_tomorrow", today=SAMPLE_TODAY, tomorrow=SAMPLE_TOMORROW
        )
        value = sensor.native_value
        assert value is not None
        prices = [_convert(b["SEK_per_kWh"], "öre/kWh") for b in SAMPLE_TOMORROW]
        assert value == round(max(prices), 4)

    def test_lowest_tomorrow(self):
        sensor = _make_sensor(
            "lowest_price_tomorrow", today=SAMPLE_TODAY, tomorrow=SAMPLE_TOMORROW
        )
        value = sensor.native_value
        assert value is not None

    def test_average_tomorrow(self):
        sensor = _make_sensor(
            "average_price_tomorrow", today=SAMPLE_TODAY, tomorrow=SAMPLE_TOMORROW
        )
        value = sensor.native_value
        assert value is not None

    def test_returns_none_before_publication(self):
        sensor = _make_sensor(
            "highest_price_tomorrow", today=SAMPLE_TODAY, tomorrow=[]
        )
        assert sensor.native_value is None


class TestExtraStateAttributes:
    """Tests for the rich attributes on the current_price sensor."""

    def test_attributes_present(self):
        now = datetime(2026, 3, 31, 10, 7, tzinfo=CET)
        with patch(
            "custom_components.elprisetjustnu.sensor.dt_util"
        ) as mock_dt:
            mock_dt.now.return_value = now

            sensor = _make_sensor(
                "current_price", today=SAMPLE_TODAY, tomorrow=SAMPLE_TOMORROW
            )
            attrs = sensor.extra_state_attributes

        assert attrs["price_area"] == "SE3"
        assert attrs["unit"] == "öre/kWh"
        assert attrs["price_trend"] in ("rising", "falling", "stable", "unknown")
        assert attrs["price_level"] in ("cheap", "normal", "expensive")
        assert attrs["data_points"] == 96
        assert attrs["tomorrow_available"] is True
        assert isinstance(attrs["tomorrow_average"], float)
        assert isinstance(attrs["all_prices_today"], list)
        assert len(attrs["all_prices_today"]) == 96

    def test_price_data_includes_tomorrow(self):
        now = datetime(2026, 3, 31, 10, 7, tzinfo=CET)
        with patch(
            "custom_components.elprisetjustnu.sensor.dt_util"
        ) as mock_dt:
            mock_dt.now.return_value = now

            sensor = _make_sensor(
                "current_price", today=SAMPLE_TODAY, tomorrow=SAMPLE_TOMORROW
            )
            attrs = sensor.extra_state_attributes

        # price_data should be today + tomorrow = 192 entries
        assert len(attrs["price_data"]) == 192

    def test_attributes_empty_when_no_data(self):
        sensor = _make_sensor("current_price", today=[])
        assert sensor.extra_state_attributes == {}

    def test_non_current_sensor_has_no_attributes(self):
        sensor = _make_sensor("highest_price_today", today=SAMPLE_TODAY)
        assert sensor.extra_state_attributes == {}

    def test_tomorrow_not_available(self):
        now = datetime(2026, 3, 31, 10, 7, tzinfo=CET)
        with patch(
            "custom_components.elprisetjustnu.sensor.dt_util"
        ) as mock_dt:
            mock_dt.now.return_value = now

            sensor = _make_sensor("current_price", today=SAMPLE_TODAY, tomorrow=[])
            attrs = sensor.extra_state_attributes

        assert attrs["tomorrow_available"] is False
        assert attrs["tomorrow_average"] is None
        # price_data should be today only = 96 entries
        assert len(attrs["price_data"]) == 96
