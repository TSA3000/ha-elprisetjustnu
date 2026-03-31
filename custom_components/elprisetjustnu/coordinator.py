"""Data update coordinator for Elpriset Just Nu."""
import logging
from datetime import datetime, timedelta

from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, UPDATE_INTERVAL_MINUTES

_LOGGER = logging.getLogger(__name__)


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

    async def _fetch_day(self, date: datetime) -> list:
        """Fetch price data for a specific date. Returns [] if not available yet."""
        url = (
            f"https://www.elprisetjustnu.se/api/v1/prices/"
            f"{date.strftime('%Y')}/{date.strftime('%m')}-{date.strftime('%d')}"
            f"_{self.region}.json"
        )
        try:
            async with self._session.get(url, timeout=10) as response:
                if response.status == 404:
                    return []
                response.raise_for_status()
                return await response.json()
        except Exception as err:
            _LOGGER.warning("Elpriset API error fetching %s: %s", url, err)
            return []

    async def _async_update_data(self) -> dict:
        """Fetch today's and tomorrow's prices."""
        now = datetime.now()
        tomorrow = now + timedelta(days=1)

        try:
            today_data = await self._fetch_day(now)
            tomorrow_data = await self._fetch_day(tomorrow)

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
                "tomorrow": tomorrow_data,
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