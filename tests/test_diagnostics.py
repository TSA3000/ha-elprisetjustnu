"""Tests for the Elpriset Just Nu diagnostics."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from custom_components.elprisetjustnu.diagnostics import (
    async_get_config_entry_diagnostics,
)

from .conftest import SAMPLE_TODAY, SAMPLE_TOMORROW


async def test_diagnostics_with_data(hass) -> None:
    """Test diagnostics output includes expected fields."""
    # Mock config entry
    entry = MagicMock()
    entry.entry_id = "test_entry_123"
    entry.data = {"region": "SE3", "unit": "öre/kWh"}
    entry.options = {}

    # Mock coordinator
    coordinator = MagicMock()
    coordinator.region = "SE3"
    coordinator.update_interval.total_seconds.return_value = 900
    coordinator.last_update_success = True
    coordinator.data = {
        "today": SAMPLE_TODAY,
        "tomorrow": SAMPLE_TOMORROW,
    }

    hass.data = {"elprisetjustnu": {"test_entry_123": coordinator}}

    result = await async_get_config_entry_diagnostics(hass, entry)

    assert result["config_entry"]["entry_id"] == "test_entry_123"
    assert result["config_entry"]["data"]["region"] == "SE3"
    assert result["coordinator"]["region"] == "SE3"
    assert result["coordinator"]["update_interval_seconds"] == 900
    assert result["coordinator"]["last_update_success"] is True
    assert result["data_summary"]["today_slots"] == 96
    assert result["data_summary"]["tomorrow_slots"] == 96
    assert result["data_summary"]["today_first"] is not None
    assert result["data_summary"]["tomorrow_last"] is not None


async def test_diagnostics_no_data(hass) -> None:
    """Test diagnostics when coordinator has no data yet."""
    entry = MagicMock()
    entry.entry_id = "test_empty"
    entry.data = {"region": "SE1", "unit": "SEK/kWh"}
    entry.options = {}

    coordinator = MagicMock()
    coordinator.region = "SE1"
    coordinator.update_interval.total_seconds.return_value = 900
    coordinator.last_update_success = False
    coordinator.data = None

    hass.data = {"elprisetjustnu": {"test_empty": coordinator}}

    result = await async_get_config_entry_diagnostics(hass, entry)

    assert result["data_summary"]["today_slots"] == 0
    assert result["data_summary"]["tomorrow_slots"] == 0
    assert result["data_summary"]["today_first"] is None
