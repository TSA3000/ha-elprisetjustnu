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
    _shift_week_dst_safe,
)

from .conftest import SAMPLE_TODAY, SAMPLE_TOMORROW, SAMPLE_LAST_WEEK_TODAY, SAMPLE_LAST_WEEK_TOMORROW, CET


# ---------------------------------------------------------------------------
# Unit conversion tests
# ---------------------------------------------------------------------------


def test_convert_ore():
    """Test SEK to öre conversion without VAT."""
    assert _convert(1.5, "öre/kWh") == 150.0
    assert _convert(0.123, "öre/kWh") == 12.3


def test_convert_sek():
    """Test SEK pass-through without VAT."""
    assert _convert(1.5, "SEK/kWh") == 1.5
    assert _convert(0.1234, "SEK/kWh") == 0.1234


def test_convert_zero():
    """Test zero price conversion."""
    assert _convert(0.0, "öre/kWh") == 0.0
    assert _convert(0.0, "SEK/kWh") == 0.0


def test_convert_with_vat():
    """Test that VAT is applied correctly."""
    # 1.0 SEK * 1.25 = 1.25 SEK = 125 öre
    assert _convert(1.0, "öre/kWh", 25) == 125.0
    assert _convert(1.0, "SEK/kWh", 25) == 1.25
    # 0% VAT = no change
    assert _convert(1.0, "öre/kWh", 0) == 100.0


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
# DST-safe shift tests
# ---------------------------------------------------------------------------


def test_shift_week_dst_safe_normal():
    """Shifting by 7 days keeps wall-clock time."""
    dt_obj = datetime(2026, 3, 17, 14, 30, tzinfo=CET)
    shifted = _shift_week_dst_safe(dt_obj)
    assert shifted.day == 24
    assert shifted.hour == 14
    assert shifted.minute == 30


def test_shift_week_dst_safe_preserves_time():
    """Wall-clock time is preserved even across months."""
    dt_obj = datetime(2026, 3, 28, 8, 0, tzinfo=CET)
    shifted = _shift_week_dst_safe(dt_obj)
    assert shifted.month == 4
    assert shifted.day == 4
    assert shifted.hour == 8
    assert shifted.minute == 0


# ---------------------------------------------------------------------------
# Sensor entity tests
# ---------------------------------------------------------------------------


def _make_coordinator_mock(today=None, tomorrow=None, lw_today=None, lw_tomorrow=None):
    """Create a mock coordinator with data."""
    coordinator = MagicMock()
    coordinator.data = {
        "today": today or [],
        "tomorrow": tomorrow or [],
        "last_week_today": lw_today or [],
        "last_week_tomorrow": lw_tomorrow or [],
    }
    return coordinator


def _make_sensor(key: str, unit: str = "öre/kWh", vat: float = 0, today=None, tomorrow=None, lw_today=None, lw_tomorrow=None):
    """Create a sensor with a mock coordinator for testing."""
    coord = _make_coordinator_mock(today, tomorrow, lw_today, lw_tomorrow)
    desc = next(d for d in SENSOR_TYPES if d.key == key)

    sensor = ElprisSensor.__new__(ElprisSensor)
    sensor.coordinator = coord
    sensor.entity_description = desc
    sensor.region = "SE3"
    sensor._unit = unit
    sensor._vat = vat
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

    def test_attributes_include_vat_info(self):
        now = datetime(2026, 3, 31, 10, 7, tzinfo=CET)
        with patch(
            "custom_components.elprisetjustnu.sensor.dt_util"
        ) as mock_dt:
            mock_dt.now.return_value = now

            sensor = _make_sensor("current_price", vat=25, today=SAMPLE_TODAY)
            attrs = sensor.extra_state_attributes

        assert attrs["vat_percent"] == 25
        assert attrs["includes_vat"] is True

    def test_attributes_vat_zero(self):
        now = datetime(2026, 3, 31, 10, 7, tzinfo=CET)
        with patch(
            "custom_components.elprisetjustnu.sensor.dt_util"
        ) as mock_dt:
            mock_dt.now.return_value = now

            sensor = _make_sensor("current_price", vat=0, today=SAMPLE_TODAY)
            attrs = sensor.extra_state_attributes

        assert attrs["vat_percent"] == 0
        assert attrs["includes_vat"] is False

    def test_unit_always_set(self):
        """Unit should always be present on the sensor (Fix #4)."""
        sensor = _make_sensor("current_price", unit="öre/kWh", today=SAMPLE_TODAY)
        assert sensor._attr_native_unit_of_measurement == "öre/kWh"

        sensor_sek = _make_sensor("current_price", unit="SEK/kWh", today=SAMPLE_TODAY)
        assert sensor_sek._attr_native_unit_of_measurement == "SEK/kWh"


class TestVATApplied:
    """Tests that VAT is correctly applied to sensor values."""

    def test_current_price_with_vat(self):
        now = datetime(2026, 3, 31, 10, 7, tzinfo=CET)
        with patch(
            "custom_components.elprisetjustnu.sensor.dt_util"
        ) as mock_dt:
            mock_dt.now.return_value = now

            sensor_no_vat = _make_sensor("current_price", vat=0, today=SAMPLE_TODAY)
            sensor_with_vat = _make_sensor("current_price", vat=25, today=SAMPLE_TODAY)

            price_no_vat = sensor_no_vat.native_value
            price_with_vat = sensor_with_vat.native_value

        assert price_no_vat is not None
        assert price_with_vat is not None
        assert price_with_vat == round(price_no_vat * 1.25, 2)

    def test_highest_price_with_vat(self):
        sensor_no_vat = _make_sensor("highest_price_today", vat=0, today=SAMPLE_TODAY)
        sensor_with_vat = _make_sensor("highest_price_today", vat=25, today=SAMPLE_TODAY)

        high_no_vat = sensor_no_vat.native_value
        high_with_vat = sensor_with_vat.native_value

        assert high_no_vat is not None
        assert high_with_vat > high_no_vat


class TestLastWeekData:
    """Tests for last week price data attributes."""

    def test_last_week_data_present(self):
        now = datetime(2026, 3, 31, 10, 7, tzinfo=CET)
        with patch(
            "custom_components.elprisetjustnu.sensor.dt_util"
        ) as mock_dt:
            mock_dt.now.return_value = now

            sensor = _make_sensor(
                "current_price",
                today=SAMPLE_TODAY,
                tomorrow=SAMPLE_TOMORROW,
                lw_today=SAMPLE_LAST_WEEK_TODAY,
                lw_tomorrow=SAMPLE_LAST_WEEK_TOMORROW,
            )
            attrs = sensor.extra_state_attributes

        assert "price_data_last_week" in attrs
        # Last week today (96) + last week tomorrow (96) = 192
        assert len(attrs["price_data_last_week"]) == 192

    def test_last_week_timestamps_shifted(self):
        """Last week timestamps should be shifted +7 days to align on chart."""
        now = datetime(2026, 3, 31, 10, 7, tzinfo=CET)
        with patch(
            "custom_components.elprisetjustnu.sensor.dt_util"
        ) as mock_dt:
            mock_dt.now.return_value = now

            sensor = _make_sensor(
                "current_price",
                today=SAMPLE_TODAY,
                lw_today=SAMPLE_LAST_WEEK_TODAY,
            )
            attrs = sensor.extra_state_attributes

        # First entry is [timestamp_ms, price] — timestamp should be March 31 (shifted from March 24)
        first_lw_ts = attrs["price_data_last_week"][0][0]
        shifted_date = datetime.fromtimestamp(first_lw_ts / 1000, tz=CET)
        assert shifted_date.date().isoformat() == "2026-03-31"

    def test_last_week_empty_when_no_data(self):
        now = datetime(2026, 3, 31, 10, 7, tzinfo=CET)
        with patch(
            "custom_components.elprisetjustnu.sensor.dt_util"
        ) as mock_dt:
            mock_dt.now.return_value = now

            sensor = _make_sensor("current_price", today=SAMPLE_TODAY)
            attrs = sensor.extra_state_attributes

        assert attrs["price_data_last_week"] == []
