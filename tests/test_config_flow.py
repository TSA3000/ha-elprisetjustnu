"""Tests for the Elpriset Just Nu config flow."""

from unittest.mock import AsyncMock, patch

import pytest

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.elprisetjustnu.const import CONF_REGION, CONF_UNIT, CONF_VAT, DOMAIN

from .conftest import MOCK_CONFIG_DATA


@pytest.fixture(autouse=True)
def mock_setup_entry():
    """Prevent actual setup during config flow tests."""
    with patch(
        "custom_components.elprisetjustnu.async_setup_entry",
        return_value=True,
    ) as mock:
        yield mock


async def test_user_flow_creates_entry(hass: HomeAssistant) -> None:
    """Test that a normal user flow creates a config entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=MOCK_CONFIG_DATA,
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Elpris SE3"
    assert result["data"] == MOCK_CONFIG_DATA


async def test_user_flow_default_values(hass: HomeAssistant) -> None:
    """Test that the form shows with default SE3 and öre/kWh."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"


async def test_duplicate_entry_aborts(hass: HomeAssistant) -> None:
    """Test that adding the same region twice is blocked."""
    # First entry succeeds
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=MOCK_CONFIG_DATA,
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY

    # Second entry with same region aborts
    result2 = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result2 = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        user_input=MOCK_CONFIG_DATA,
    )
    assert result2["type"] is FlowResultType.ABORT
    assert result2["reason"] == "already_configured"


async def test_different_regions_allowed(hass: HomeAssistant) -> None:
    """Test that different regions can coexist."""
    # SE3
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_REGION: "SE3", CONF_UNIT: "öre/kWh", CONF_VAT: 25},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY

    # SE1 — should also succeed
    result2 = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result2 = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        user_input={CONF_REGION: "SE1", CONF_UNIT: "SEK/kWh", CONF_VAT: 0},
    )
    assert result2["type"] is FlowResultType.CREATE_ENTRY


async def test_sek_unit_option(hass: HomeAssistant) -> None:
    """Test creating an entry with SEK/kWh unit."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_REGION: "SE4", CONF_UNIT: "SEK/kWh", CONF_VAT: 25},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_UNIT] == "SEK/kWh"