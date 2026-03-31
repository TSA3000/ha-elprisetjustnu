import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector

from .const import DOMAIN, CONF_REGION, CONF_UNIT, REGIONS, UNITS


class ElprisetJustNuConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Elpriset Just Nu."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(
                title=f"Elpris {user_input[CONF_REGION]}",
                data=user_input,
            )

        data_schema = vol.Schema({
            vol.Required(CONF_REGION, default="SE3"): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=REGIONS,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required(CONF_UNIT, default="öre/kWh"): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=UNITS,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
        })

        return self.async_show_form(step_id="user", data_schema=data_schema)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return ElprisetJustNuOptionsFlowHandler()


class ElprisetJustNuOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle the Options Flow (the Configure button)."""

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_region = self.config_entry.options.get(
            CONF_REGION, self.config_entry.data.get(CONF_REGION)
        )
        current_unit = self.config_entry.options.get(
            CONF_UNIT, self.config_entry.data.get(CONF_UNIT, "öre/kWh")
        )

        options_schema = vol.Schema({
            vol.Required(CONF_REGION, default=current_region): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=REGIONS,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required(CONF_UNIT, default=current_unit): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=UNITS,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
        })

        return self.async_show_form(step_id="init", data_schema=options_schema)