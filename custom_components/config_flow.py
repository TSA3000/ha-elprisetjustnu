import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import DOMAIN, CONF_REGION, REGIONS

class ElprisetJustNuConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Elpriset Just Nu."""
    
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step where the user selects a region during installation."""
        if user_input is not None:
            region = user_input[CONF_REGION]
            return self.async_create_entry(
                title=f"Elpris {region}", 
                data=user_input
            )

        # Build a native modern dropdown for the regions
        data_schema = vol.Schema({
            vol.Required(CONF_REGION, default="SE3"): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=REGIONS,
                    mode=selector.SelectSelectorMode.DROPDOWN
                )
            )
        })

        return self.async_show_form(
            step_id="user", 
            data_schema=data_schema
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Tell Home Assistant that this integration supports an Options Flow."""
        return ElprisetJustNuOptionsFlowHandler()


class ElprisetJustNuOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle the Options Flow (the 'Configure' button)."""

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            # Save the newly selected region into the config entry options
            return self.async_create_entry(title="", data=user_input)

        # Find out what the current region is so we can pre-select it in the dropdown
        current_region = self.config_entry.options.get(
            CONF_REGION, self.config_entry.data.get(CONF_REGION)
        )

        options_schema = vol.Schema({
            vol.Required(CONF_REGION, default=current_region): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=REGIONS,
                    mode=selector.SelectSelectorMode.DROPDOWN
                )
            )
        })

        return self.async_show_form(
            step_id="init", 
            data_schema=options_schema
        )