"""Tests for the Elpriset Just Nu config flow."""

from unittest.mock import AsyncMock, patch

import pytest

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.elprisetjustnu.const import (
    CONF_REGION,
    CONF_UNIT,
    CONF_INCLUDE_VAT,
    CONF_VAT,
    CONF_SHOW_UNIT,
    DOMAIN,
)

from .conftest import MOCK_CONFIG_DATA


def _input(region="SE3", unit="öre/kWh", include_vat=True, vat=25.0, show_unit=True):
    """Build a complete user_input dict."""
    return {
        CONF_REGION: region,
        CONF_UNIT: unit,
        CONF_INCLUDE_VAT: include_vat,
        CONF_VAT: vat,
        CONF_SHOW_UNIT: show_unit,
    }


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
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=MOCK_CONFIG_DATA,
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY

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
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=_input(region="SE3"),
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY

    result2 = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result2 = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        user_input=_input(region="SE1", unit="SEK/kWh", vat=0.0),
    )
    assert result2["type"] is FlowResultType.CREATE_ENTRY


async def test_sek_unit_option(hass: HomeAssistant) -> None:
    """Test creating an entry with SEK/kWh unit."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=_input(region="SE4", unit="SEK/kWh"),
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_UNIT] == "SEK/kWh"


async def test_vat_disabled(hass: HomeAssistant) -> None:
    """Test creating an entry with VAT disabled."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=_input(region="SE2", include_vat=False),
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_INCLUDE_VAT] is False


async def test_unit_hidden(hass: HomeAssistant) -> None:
    """Test creating an entry with unit hidden."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=_input(region="SE4", show_unit=False),
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_SHOW_UNIT] is False