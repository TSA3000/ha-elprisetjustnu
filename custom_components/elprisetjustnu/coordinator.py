"""Data update coordinator for Elpriset Just Nu."""
import logging
from datetime import datetime, timedelta

from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, UPDATE_INTERVAL_MINUTES

_LOGGER = logging.getLogger(__name__)


class ElprisetCoordinator(DataUpdateCoordinator):
    """Coordinator that fetches price data from the Elpriset Just Nu API."""

    def __init__(self, hass, region: str) -> None:
        """Initialise the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{region.lower()}",
            update_interval=timedelta(minutes=UPDATE_INTERVAL_MINUTES),
        )
        self.region = region
        self._session = async_get_clientsession(hass)
        self._last_known_data: list = []

    async def _async_update_data(self) -> list:
        """Fetch today's price data from the API."""
        now = datetime.now()
        url = (
            f"https://www.elprisetjustnu.se/api/v1/prices/"
            f"{now.strftime('%Y')}/{now.strftime('%m')}-{now.strftime('%d')}"
            f"_{self.region}.json"
        )

        try:
            async with self._session.get(url, timeout=10) as response:
                if response.status == 404:
                    _LOGGER.debug(
                        "Elpriset API: prices not yet published for today (404) — "
                        "using last known data"
                    )
                    return self._last_known_data or []

                response.raise_for_status()
                data = await response.json()
                self._last_known_data = data
                _LOGGER.debug(
                    "Elpriset API: fetched %d price slots for %s",
                    len(data),
                    self.region,
                )
                return data

        except Exception as err:
            if self._last_known_data:
                _LOGGER.warning(
                    "Elpriset API error, keeping last known data: %s", err
                )
                return self._last_known_data
            raise UpdateFailed(
                f"Error fetching Elpriset data for {self.region}: {err}"
            ) from err