"""Config flow for Tech Sterowniki integration."""
import logging
from typing import List
import uuid

import voluptuous as vol

from homeassistant import config_entries, core, exceptions
from homeassistant.config_entries import ConfigEntry
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import aiohttp_client, config_validation as cv

from .const import DOMAIN
from .tech import Tech, TechError, TechLoginError

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required("username"): cv.string,
        vol.Required("password"): cv.string,
    }
)


def controllers_schema(controllers) -> vol.Schema:
    """Return the data schema for controllers."""

    return vol.Schema(
        {
            vol.Optional("controllers"): cv.multi_select(
                {
                    str(controller["controller"]["id"]): controller["controller"][
                        "name"
                    ]
                    for controller in controllers
                }
            )
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

    # Return info that you want to store in the config entry.
    return {
        "user_id": api.user_id,
        "token": api.token,
        "controllers": modules,
    }


@config_entries.HANDLERS.register(DOMAIN)
class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Tech Sterowniki."""

    VERSION = 1
    # Pick one of the available connection classes in homeassistant/config_entries.py
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._init_info: dict[str, str] | None = None
        self._controllers: List[dict] | None = None

    async def _async_finish_controller(self, user_input: dict[str, str]) -> FlowResult:
        """Finish setting up controllers."""

        if not user_input["controllers"]:
            return self.async_abort(reason="no_modules")

        if self._controllers is not None and user_input is not None:
            controllers = user_input["controllers"]

            if len(controllers) == 0:
                return self.async_abort(reason="no_modules")

            # check if we have any of the selected controllers already configured
            # and abort if so
            for controller_id in controllers:
                controller = next(
                    obj
                    for obj in self._controllers
                    if obj["controller"].get("id") == int(controller_id)
                )
                await self.async_set_unique_id(controller["controller"]["udid"])
                self._abort_if_unique_id_configured()

            # process first controllers and add config entries for them
            if len(controllers) > 1:
                for controller_id in controllers[1 : len(controllers)]:
                    controller = next(
                        obj
                        for obj in self._controllers
                        if obj["controller"].get("id") == int(controller_id)
                    )
                    await self.async_set_unique_id(controller["controller"]["udid"])

                    _LOGGER.debug("Adding config entry for: %s", controller)

                    await self.hass.config_entries.async_add(
                        self._create_config_entry(controller=controller)
                    )

            # process last controller and async create entry finishing the step
            controller_udid = next(
                obj
                for obj in self._controllers
                if obj["controller"].get("id") == int(controllers[0])
            )["controller"]["udid"]

            await self.async_set_unique_id(controller_udid)

            return self.async_create_entry(
                title=next(
                    obj
                    for obj in self._controllers
                    if obj["controller"].get("id") == int(controllers[0])
                )["controller"]["name"],
                data=next(
                    obj
                    for obj in self._controllers
                    if obj["controller"].get("id") == int(controllers[0])
                ),
            )

    async def async_step_select_controllers(
        self,
        user_input: dict[str, str] | None = None,
    ) -> FlowResult:
        """Handle the selection of controllers."""
        if not user_input:
            self._controllers = self._create_controllers_array(
                validated_input=self._init_info
            )

            return self.async_show_form(
                step_id="select_controllers",
                data_schema=controllers_schema(controllers=self._controllers),
            )

        return await self._async_finish_controller(user_input)

    async def async_step_user(self, user_input: dict[str, str] | None = None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)

                # Store info to use in next step
                self._init_info = info

                return await self.async_step_select_controllers()
            except TechLoginError:
                errors["base"] = "invalid_auth"
            except TechError:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )

    def _create_config_entry(self, controller: dict) -> ConfigEntry:
        return ConfigEntry(
            data=controller,
            title=controller["controller"]["name"],
            entry_id=uuid.uuid4().hex,
            domain=DOMAIN,
            version=ConfigFlow.VERSION,
            minor_version=ConfigFlow.MINOR_VERSION,
            source=ConfigFlow.CONNECTION_CLASS,
        )

    def _create_controllers_array(self, validated_input: dict) -> List[dict]:
        return [
            self._create_controller_dict(validated_input, controller_dict)
            for controller_dict in validated_input["controllers"]
        ]

    def _create_controller_dict(
        self, validated_input: dict, controller_dict: dict
    ) -> dict:
        return {
            "user_id": validated_input["user_id"],
            "token": validated_input["token"],
            "controller": controller_dict,
            "version": controller_dict["version"] + ": " + controller_dict["name"],
        }


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(exceptions.HomeAssistantError):
    """Error to indicate there is invalid auth."""
