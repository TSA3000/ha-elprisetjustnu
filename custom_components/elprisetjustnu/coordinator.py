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
        # Last week cache — only needs to be fetched once per day
        self._last_week_today: list = []
        self._last_week_tomorrow: list = []
        self._last_week_fetched_date = None

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
        """Fetch today's, tomorrow's, and last week's prices."""
        now = dt_util.now()
        today = now.date()
        tomorrow = today + timedelta(days=1)

        # Clear stale tomorrow cache when the date rolls over.
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

            # Tomorrow data is only available after ~13:00 CET
            if tomorrow_data:
                self._last_known_tomorrow = tomorrow_data

            # Fetch last week's data (same weekday) — cache per day
            if self._last_week_fetched_date != today:
                last_week_today = today - timedelta(days=7)
                last_week_tomorrow = tomorrow - timedelta(days=7)

                self._last_week_today = await self._fetch_day(
                    last_week_today.year, last_week_today.month, last_week_today.day
                )
                self._last_week_tomorrow = await self._fetch_day(
                    last_week_tomorrow.year, last_week_tomorrow.month, last_week_tomorrow.day
                )
                self._last_week_fetched_date = today

                _LOGGER.debug(
                    "Elpriset %s — last week: today=%d slots, tomorrow=%d slots",
                    self.region,
                    len(self._last_week_today),
                    len(self._last_week_tomorrow),
                )

            _LOGGER.debug(
                "Elpriset %s — today: %d slots, tomorrow: %d slots",
                self.region,
                len(today_data),
                len(self._last_known_tomorrow),
            )

            return {
                "today": today_data,
                "tomorrow": self._last_known_tomorrow,
                "last_week_today": self._last_week_today,
                "last_week_tomorrow": self._last_week_tomorrow,
            }

        except Exception as err:
            if self._last_known_today:
                _LOGGER.warning(
                    "Elpriset API error, using last known data: %s", err
                )
                return {
                    "today": self._last_known_today,
                    "tomorrow": self._last_known_tomorrow,
                    "last_week_today": self._last_week_today,
                    "last_week_tomorrow": self._last_week_tomorrow,
                }
            raise UpdateFailed(
                f"Error fetching Elpriset data for {self.region}: {err}"
            ) from err
