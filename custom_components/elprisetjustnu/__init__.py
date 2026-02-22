from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Elpriset Just Nu from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    # Listen for options updates and reload the integration if they change!
    entry.async_on_unload(entry.add_update_listener(update_listener))
    
    # Forward the setup to the sensor platform
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, ["sensor"])

async def update_listener(hass: HomeAssistant, entry: ConfigEntry):
    """Reload the integration automatically if the user changes the region."""
    await hass.config_entries.async_reload(entry.entry_id)