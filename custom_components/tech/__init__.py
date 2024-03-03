"""The Tech Controllers integration."""
import asyncio
import logging

from aiohttp import ClientSession
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from . import assets
from .const import API_TIMEOUT, CONTROLLER, DOMAIN, SCAN_INTERVAL, UDID, USER_ID
from .tech import Tech, TechError, TechLoginError

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
    user_id = entry.data[USER_ID]
    token = entry.data[CONF_TOKEN]
    # Store an API object for your platforms to access
    hass.data.setdefault(DOMAIN, {})
    websession = async_get_clientsession(hass)

    coordinator = TechCoordinator(hass, websession, user_id, token)
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await coordinator.async_config_entry_first_refresh()

    await assets.load_subtitles(language_code, Tech(websession, user_id, token))

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


class TechCoordinator(DataUpdateCoordinator):
    """TECH API data update coordinator."""

    config_entry: ConfigEntry

    def __init__(
        self, hass: HomeAssistant, session: ClientSession, user_id: str, token: str
    ) -> None:
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name=DOMAIN,
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=SCAN_INTERVAL,
        )
        self.api = Tech(session, user_id, token)

    async def _async_update_data(self):
        """Fetch data from TECH API endpoint(s)."""

        _LOGGER.debug("_async_update_data: %s", str(self.config_entry.data))

        try:
            async with asyncio.timeout(API_TIMEOUT):
                return await self.api.module_data(
                    self.config_entry.data[CONTROLLER][UDID]
                )
        except TechLoginError as err:
            raise ConfigEntryAuthFailed from err
        except TechError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
