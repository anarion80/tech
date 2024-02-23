"""Config flow for Tech Sterowniki integration."""
import logging
from typing import List
import uuid

import voluptuous as vol

from homeassistant import config_entries, core, exceptions
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import aiohttp_client

from .const import DOMAIN  # pylint:disable=unused-import
from .tech import Tech

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required("username"): str,
        vol.Required("password"): str,
    }
)


async def validate_input(hass: core.HomeAssistant, data):
    """Validate the user input allows us to connect.

    Data has the keys from DATA_SCHEMA with values provided by the user.
    """

    http_session = aiohttp_client.async_get_clientsession(hass)
    api = Tech(http_session)

    if not await api.authenticate(data["username"], data["password"]):
        raise InvalidAuth
    modules = await api.list_modules()

    # If you cannot connect:
    # throw CannotConnect
    # If the authentication is wrong:
    # InvalidAuth

    # Return info that you want to store in the config entry.
    return {"user_id": api.user_id, "token": api.token, "modules": modules}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Tech Sterowniki."""

    VERSION = 1
    # Pick one of the available connection classes in homeassistant/config_entries.py
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            try:
                _LOGGER.debug("Context: %s", str(self.context))
                validated_input = await validate_input(self.hass, user_input)

                modules = self._create_modules_array(validated_input=validated_input)

                if len(modules) == 0:
                    return self.async_abort(reason="no_modules")

                if len(modules) > 1:
                    for module in modules[1 : len(modules)]:
                        await self.hass.config_entries.async_add(
                            self._create_config_entry(module=module)
                        )

                return self.async_create_entry(
                    title=modules[0]["version"], data=modules[0]
                )
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )

    def _create_config_entry(self, module: dict) -> ConfigEntry:
        return ConfigEntry(
            data=module,
            title=module["version"],
            entry_id=uuid.uuid4().hex,
            domain=DOMAIN,
            version=ConfigFlow.VERSION,
            minor_version=ConfigFlow.MINOR_VERSION,
            source=ConfigFlow.CONNECTION_CLASS,
        )

    def _create_modules_array(self, validated_input: dict) -> List[dict]:
        return [
            self._create_module_dict(validated_input, module_dict)
            for module_dict in validated_input["modules"]
        ]

    def _create_module_dict(self, validated_input: dict, module_dict: dict) -> dict:
        return {
            "user_id": validated_input["user_id"],
            "token": validated_input["token"],
            "module": module_dict,
            "version": module_dict["version"] + ": " + module_dict["name"],
        }


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(exceptions.HomeAssistantError):
    """Error to indicate there is invalid auth."""
