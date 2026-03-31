"""Data update coordinator for Elpriset Just Nu."""

import asyncio
import logging
from datetime import timedelta

import aiohttp
from aiohttp import ClientTimeout

from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import DOMAIN, UPDATE_INTERVAL_MINUTES

_LOGGER = logging.getLogger(__name__)

API_TIMEOUT = ClientTimeout(total=10)


class ElprisetCoordinator(DataUpdateCoordinator):
    """Fetches today's and tomorrow's price data from the Elpriset Just Nu API."""

    def __init__(self, hass, region: str) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{region.lower()}",
            update_interval=timedelta(minutes=UPDATE_INTERVAL_MINUTES),
        )
        self.region = region
        self._session = async_get_clientsession(hass)
        self._last_known_today: list = []
        self._last_known_tomorrow: list = []
        self._last_date = None

    async def _fetch_day(self, year: int, month: int, day: int) -> list:
        """Fetch price data for a specific date. Returns [] if not available yet."""
        url = (
            f"https://www.elprisetjustnu.se/api/v1/prices/"
            f"{year}/{month:02d}-{day:02d}_{self.region}.json"
        )
        try:
            async with self._session.get(url, timeout=API_TIMEOUT) as response:
                if response.status == 404:
                    return []
                response.raise_for_status()
                return await response.json()
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            _LOGGER.warning("Elpriset API error fetching %s: %s", url, err)
            return []

    async def _async_update_data(self) -> dict:
        """Fetch today's and tomorrow's prices."""
        now = dt_util.now()
        today = now.date()
        tomorrow = today + timedelta(days=1)

        # Clear stale tomorrow cache when the date rolls over.
        # Yesterday's "tomorrow" data is now "today" — the API will serve it fresh.
        if self._last_date is not None and today != self._last_date:
            _LOGGER.debug("Date changed from %s to %s — clearing tomorrow cache", self._last_date, today)
            self._last_known_tomorrow = []
        self._last_date = today

        try:
            today_data = await self._fetch_day(today.year, today.month, today.day)
            tomorrow_data = await self._fetch_day(tomorrow.year, tomorrow.month, tomorrow.day)

            # Keep last known good data for today
            if today_data:
                self._last_known_today = today_data
            else:
                today_data = self._last_known_today

            # Tomorrow data is only available after ~13:00 CET — empty until then
            if tomorrow_data:
                self._last_known_tomorrow = tomorrow_data

            _LOGGER.debug(
                "Elpriset %s — today: %d slots, tomorrow: %d slots",
                self.region,
                len(today_data),
                len(tomorrow_data),
            )

            return {
                "today": today_data,
                "tomorrow": self._last_known_tomorrow,
            }

        except Exception as err:
            if self._last_known_today:
                _LOGGER.warning(
                    "Elpriset API error, using last known data: %s", err
                )
                return {
                    "today": self._last_known_today,
                    "tomorrow": self._last_known_tomorrow,
                }
            raise UpdateFailed(
                f"Error fetching Elpriset data for {self.region}: {err}"
            ) from err
