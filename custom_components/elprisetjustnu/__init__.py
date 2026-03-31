"""Elpriset Just Nu integration."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, CONF_REGION, PLATFORMS
from .coordinator import ElprisetCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Elpriset Just Nu from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    region = entry.options.get(CONF_REGION, entry.data.get(CONF_REGION))

    coordinator = ElprisetCoordinator(hass, region)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    entry.async_on_unload(entry.add_update_listener(update_listener))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the integration when the user changes options."""
    await hass.config_entries.async_reload(entry.entry_id)
