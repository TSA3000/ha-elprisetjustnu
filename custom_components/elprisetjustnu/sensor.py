"""Sensor platform for Elpriset Just Nu."""
import logging
from datetime import datetime, timedelta
import dateutil.parser

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
    SensorEntityDescription,
)
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
    CoordinatorEntity,
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN, CONF_REGION, UPDATE_INTERVAL_MINUTES

_LOGGER = logging.getLogger(__name__)

# Define the blueprints for our three sensors
SENSOR_TYPES: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="current_price",
        name="Current Price",
        icon="mdi:currency-sek",
        native_unit_of_measurement="öre/kWh",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="highest_price_today",
        name="Highest Price",
        icon="mdi:arrow-up-bold-circle-outline",
        native_unit_of_measurement="öre/kWh",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="lowest_price_today",
        name="Lowest Price",
        icon="mdi:arrow-down-bold-circle-outline",
        native_unit_of_measurement="öre/kWh",
        device_class=SensorDeviceClass.MONETARY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the Elpriset Just Nu sensor platform."""
    
    # Read the region from options if available (Configure flow), otherwise fallback to initial data
    region = entry.options.get(CONF_REGION, entry.data.get(CONF_REGION))
    session = async_get_clientsession(hass)

    async def async_update_data():
        """Fetch the latest pricing data from the API."""
        now = datetime.now()
        year = now.strftime("%Y")
        month = now.strftime("%m")
        day = now.strftime("%d")

        url = f"https://www.elprisetjustnu.se/api/v1/prices/{year}/{month}-{day}_{region}.json"

        try:
            async with session.get(url) as response:
                response.raise_for_status()
                return await response.json()
        except Exception as err:
            raise UpdateFailed(f"Error communicating with Elpriset API: {err}")

    # Set up the background coordinator
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"elprisetjustnu_{region}_coordinator",
        update_method=async_update_data,
        update_interval=timedelta(minutes=UPDATE_INTERVAL_MINUTES),
    )

    # Fetch initial data before loading entities
    await coordinator.async_config_entry_first_refresh()

    # Create and add all three entities
    entities = [
        ElprisSensor(coordinator, region, description, entry.entry_id)
        for description in SENSOR_TYPES
    ]

    async_add_entities(entities)


class ElprisSensor(CoordinatorEntity, SensorEntity):
    """Representation of an individual Elpris Sensor."""

    def __init__(
        self,
        coordinator: DataUpdateCoordinator,
        region: str,
        description: SensorEntityDescription,
        entry_id: str,
    ):
        """Initialize the sensor."""
        super().__init__(coordinator)
        
        self.entity_description = description
        self.region = region
        
        # Set unique ID and display name dynamically
        self._attr_unique_id = f"{entry_id}_{region.lower()}_{description.key}"
        self._attr_name = f"Elpris {region} {description.name}"

        # Group these sensors together under one Device in Home Assistant
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name=f"Elpriset Just Nu ({region})",
            manufacturer="Elpriset Just Nu",
            model="Elpris API",
            configuration_url="https://www.elprisetjustnu.se/elpris-api",
        )

    @property
    def native_value(self):
        """Return the calculated state of the sensor in öre/kWh."""
        if not self.coordinator.data:
            return None

        # Extract all SEK prices and convert them to öre (* 100)
        prices_in_ore = [price_block["SEK_per_kWh"] * 100 for price_block in self.coordinator.data]

        if self.entity_description.key == "highest_price_today":
            return round(max(prices_in_ore), 2)

        elif self.entity_description.key == "lowest_price_today":
            return round(min(prices_in_ore), 2)

        elif self.entity_description.key == "current_price":
            now = datetime.now().astimezone()
            
            for price_block in self.coordinator.data:
                start_time = dateutil.parser.parse(price_block["time_start"])
                end_time = dateutil.parser.parse(price_block["time_end"])

                # Check if the current time falls within this specific price block
                if start_time <= now < end_time:
                    return round(price_block["SEK_per_kWh"] * 100, 2)

        return None