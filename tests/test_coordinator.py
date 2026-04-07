"""Tests for the Elpriset Just Nu data coordinator."""

from __future__ import annotations

import asyncio
from datetime import datetime, date, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.elprisetjustnu.coordinator import ElprisetCoordinator

from .conftest import SAMPLE_TODAY, SAMPLE_TOMORROW, CET


def _mock_response(status: int = 200, json_data: list | None = None):
    """Create a mock aiohttp response as an async context manager."""
    response = AsyncMock()
    response.status = status
    response.raise_for_status = MagicMock()
    if status == 404:
        pass  # json won't be called
    else:
        response.json = AsyncMock(return_value=json_data or [])

    cm = AsyncMock()
    cm.__aenter__ = AsyncMock(return_value=response)
    cm.__aexit__ = AsyncMock(return_value=False)
    return cm


def _responses_4(today_s=200, today_d=None, tomorrow_s=200, tomorrow_d=None,
                  lw_today_s=200, lw_today_d=None, lw_tomorrow_s=200, lw_tomorrow_d=None):
    """Build a 4-response list for a first fetch (today, tomorrow, lw_today, lw_tomorrow)."""
    return [
        _mock_response(today_s, today_d),
        _mock_response(tomorrow_s, tomorrow_d),
        _mock_response(lw_today_s, lw_today_d),
        _mock_response(lw_tomorrow_s, lw_tomorrow_d),
    ]


@pytest.fixture
def mock_now():
    """Patch dt_util.now to return a fixed time: 2026-03-31 10:07 CET."""
    fixed = datetime(2026, 3, 31, 10, 7, 0, tzinfo=CET)
    with patch(
        "custom_components.elprisetjustnu.coordinator.dt_util"
    ) as mock_dt:
        mock_dt.now.return_value = fixed
        yield mock_dt


@pytest.fixture
def coordinator(hass: HomeAssistant, mock_now):
    """Create a coordinator with a mocked session."""
    with patch(
        "custom_components.elprisetjustnu.coordinator.async_get_clientsession"
    ) as mock_get_session:
        session = AsyncMock()
        mock_get_session.return_value = session
        coord = ElprisetCoordinator(hass, "SE3")
        coord._session = session
        yield coord


async def test_fetch_today_and_tomorrow(coordinator: ElprisetCoordinator) -> None:
    """Test successful fetch of today and tomorrow data."""
    coordinator._session.get = MagicMock(side_effect=_responses_4(
        today_d=SAMPLE_TODAY, tomorrow_d=SAMPLE_TOMORROW,
    ))

    data = await coordinator._async_update_data()

    assert len(data["today"]) == 96
    assert len(data["tomorrow"]) == 96
    assert data["today"][0]["SEK_per_kWh"] == SAMPLE_TODAY[0]["SEK_per_kWh"]
    assert "last_week_today" in data
    assert "last_week_tomorrow" in data


async def test_tomorrow_404_returns_empty(coordinator: ElprisetCoordinator) -> None:
    """Test that a 404 for tomorrow returns empty list (not yet published)."""
    coordinator._session.get = MagicMock(side_effect=_responses_4(
        today_d=SAMPLE_TODAY, tomorrow_s=404,
    ))

    data = await coordinator._async_update_data()

    assert len(data["today"]) == 96
    assert data["tomorrow"] == []


async def test_today_404_uses_cache(coordinator: ElprisetCoordinator) -> None:
    """Test that if today returns 404, last known data is used."""
    # First successful fetch (4 calls: today, tomorrow, lw_today, lw_tomorrow)
    coordinator._session.get = MagicMock(side_effect=_responses_4(
        today_d=SAMPLE_TODAY, tomorrow_s=404,
    ))
    data1 = await coordinator._async_update_data()
    assert len(data1["today"]) == 96

    # Second fetch — today returns empty, last week already cached (only 2 calls)
    coordinator._session.get = MagicMock(side_effect=[
        _mock_response(404),
        _mock_response(404),
    ])
    data2 = await coordinator._async_update_data()
    assert len(data2["today"]) == 96  # cached


async def test_network_error_uses_cache(coordinator: ElprisetCoordinator) -> None:
    """Test that network errors fall back to cached data."""
    # First successful fetch
    coordinator._session.get = MagicMock(side_effect=_responses_4(
        today_d=SAMPLE_TODAY, tomorrow_d=SAMPLE_TOMORROW,
    ))
    await coordinator._async_update_data()

    # Network error on second fetch
    def raise_client_error(*args, **kwargs):
        cm = AsyncMock()
        cm.__aenter__ = AsyncMock(side_effect=aiohttp.ClientError("timeout"))
        cm.__aexit__ = AsyncMock(return_value=False)
        return cm

    coordinator._session.get = MagicMock(side_effect=raise_client_error)
    data = await coordinator._async_update_data()

    # Should still return cached data
    assert len(data["today"]) == 96


async def test_network_error_no_cache_raises(coordinator: ElprisetCoordinator) -> None:
    """Test that a network error with no cache raises UpdateFailed.

    _fetch_day catches its own errors, so we mock it directly to simulate
    an unexpected failure in _async_update_data's outer try block.
    """
    with patch.object(
        coordinator, "_fetch_day", new_callable=AsyncMock, side_effect=Exception("unexpected")
    ):
        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()


async def test_midnight_clears_tomorrow_cache(coordinator: ElprisetCoordinator) -> None:
    """Test that stale tomorrow data is cleared when the date rolls over."""
    # Fetch on March 31
    coordinator._session.get = MagicMock(side_effect=_responses_4(
        today_d=SAMPLE_TODAY, tomorrow_d=SAMPLE_TOMORROW,
    ))
    data = await coordinator._async_update_data()
    assert len(data["tomorrow"]) == 96

    # Simulate date change to April 1
    new_now = datetime(2026, 4, 1, 0, 15, 0, tzinfo=CET)
    with patch(
        "custom_components.elprisetjustnu.coordinator.dt_util"
    ) as mock_dt:
        mock_dt.now.return_value = new_now

        # 4 calls: April 1 data, April 2 (404), last week March 25, March 26
        coordinator._session.get = MagicMock(side_effect=_responses_4(
            today_d=SAMPLE_TODAY, tomorrow_s=404,
        ))
        data = await coordinator._async_update_data()

    # Tomorrow cache should have been cleared at midnight
    assert data["tomorrow"] == []


async def test_api_url_format(coordinator: ElprisetCoordinator) -> None:
    """Test that the API URL is correctly formatted."""
    calls = []

    def capture_get(url, **kwargs):
        calls.append(url)
        return _mock_response(200, [])

    coordinator._session.get = MagicMock(side_effect=capture_get)
    await coordinator._async_update_data()

    # 4 calls: today, tomorrow, last_week_today, last_week_tomorrow
    assert len(calls) == 4
    assert "2026/03-31_SE3.json" in calls[0]
    assert "2026/04-01_SE3.json" in calls[1]
    assert "2026/03-24_SE3.json" in calls[2]
    assert "2026/03-25_SE3.json" in calls[3]


async def test_last_week_cached_per_day(coordinator: ElprisetCoordinator) -> None:
    """Test that last week data is only fetched once per day."""
    calls = []

    def capture_get(url, **kwargs):
        calls.append(url)
        return _mock_response(200, [])

    coordinator._session.get = MagicMock(side_effect=capture_get)

    # First fetch — 4 calls
    await coordinator._async_update_data()
    assert len(calls) == 4

    # Second fetch same day — only 2 calls (last week cached)
    calls.clear()
    coordinator._session.get = MagicMock(side_effect=capture_get)
    await coordinator._async_update_data()
    assert len(calls) == 2
