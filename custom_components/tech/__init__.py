"""The Tech Controllers integration."""
import asyncio
import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import aiohttp_client

from . import assets
from .const import DOMAIN
from .tech import Tech

_LOGGER = logging.getLogger(__name__)
CONFIG_SCHEMA = vol.Schema({DOMAIN: vol.Schema({})}, extra=vol.ALLOW_EXTRA)

# List the platforms that you want to support.
PLATFORMS = ["climate", "sensor", "binary_sensor"]


async def async_setup(hass: HomeAssistant, config: dict):  # pylint: disable=unused-argument
    """Set up the Tech Controllers component."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Tech Controllers from a config entry."""
    _LOGGER.debug("Setting up component's entry.")
    _LOGGER.debug("Entry id: %s", str(entry.entry_id))
    _LOGGER.debug(
        "Entry -> title: %s, data: %s, id: %s, domain: %s",
        entry.title,
        str(entry.data),
        entry.entry_id,
        entry.domain,
    )
    language_code = hass.config.language
    # Store an API object for your platforms to access
    hass.data.setdefault(DOMAIN, {})
    http_session = aiohttp_client.async_get_clientsession(hass)
    hass.data[DOMAIN][entry.entry_id] = Tech(
        http_session, entry.data["user_id"], entry.data["token"]
    )
    api = hass.data[DOMAIN][entry.entry_id]

    await assets.load_subtitles(language_code, api)

    _LOGGER.debug("Setting up component's entry for Platforms: %s", PLATFORMS)
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
