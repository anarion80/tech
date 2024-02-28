"""Config flow for Tech Sterowniki integration."""
import logging
from typing import Any, List
import uuid

import voluptuous as vol

from homeassistant import config_entries, core, exceptions
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import aiohttp_client, config_validation as cv

from .const import DOMAIN
from .tech import Tech

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required("username"): cv.string,
        vol.Required("password"): cv.string,
    }
)

# def controllers_schema(controllers) -> vol.Schema:
#     """Return the data schema for controllers."""

#     schema = {}
#     _LOGGER.debug("🚀 ~ controllers: %s", controllers)
#     for controller in controllers:
#         _LOGGER.debug(
#             "🚀 ~ controllers_schema:controller: %s", controller["controller"]["name"]
#         )
#         schema[
#             vol.Optional(
#                 controller["controller"]["name"],
#                 default=True,
#                 description={"suggested_value": "test"},
#             )
#         ] = cv.boolean
#         _LOGGER.debug("CONTROLLER_DATA_SCHEMA inside: %s", schema)
#     _LOGGER.debug("CONTROLLER_DATA_SCHEMA: %s", schema)
#     return vol.Schema(schema)


def controllers_schema(controllers) -> vol.Schema:
    """Return the data schema for controllers."""

    # schema = {}
    # _LOGGER.debug("🚀 ~ controllers: %s", controllers)
    # for controller in controllers:
    #     _LOGGER.debug(
    #         "🚀 ~ controllers_schema:controller: %s", controller["controller"]["name"]
    #     )
    #     schema[
    #         vol.Optional(
    #             controller["controller"]["name"],
    #             default=True,
    #             description={"suggested_value": "test"},
    #         )
    #     ] = cv.boolean
    #     _LOGGER.debug("CONTROLLER_DATA_SCHEMA inside: %s", schema)
    # _LOGGER.debug("CONTROLLER_DATA_SCHEMA: %s", schema)
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


# def controllers_schema(controllers) -> vol.Schema:
#     """Return the data schema for controllers."""

#     schema = []
#     _LOGGER.debug("🚀 ~ controllers: %s", controllers)
#     for controller in controllers:
#         _LOGGER.debug(
#             "🚀 ~ controllers_schema:controller: %s", controller["controller"]["name"]
#         )
#         schema.append(controller["controller"]["name"])
#         _LOGGER.debug("CONTROLLER_DATA_SCHEMA inside: %s", schema)
#     _LOGGER.debug("CONTROLLER_DATA_SCHEMA: %s", schema)
#     return vol.Schema({vol.Optional("controllers"): vol.In(schema)})


# def controllers_schema(controllers) -> vol.Schema:
#     """Return the data schema for controllers."""

#     schema = []
#     _LOGGER.debug("🚀 ~ controllers: %s", controllers)
#     for controller in controllers:
#         _LOGGER.debug(
#             "🚀 ~ controllers_schema:controller: %s", controller["controller"]["name"]
#         )
#         schema.append({vol.Optional(controller["controller"]["name"]): cv.boolean})
#         _LOGGER.debug("CONTROLLER_DATA_SCHEMA inside: %s", schema)
#     _LOGGER.debug("CONTROLLER_DATA_SCHEMA: %s", schema)
#     return vol.Schema(schema)


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

        errors = {}
        _LOGGER.debug("🚀 ~ _async_finish_controller:user_input: %s", user_input)
        _LOGGER.debug("🚀 ~ _async_finish_controller:_init_info: %s", self._init_info)
        _LOGGER.debug(
            "🚀 ~ _async_finish_controller:_controllers: %s", self._controllers
        )

        if not user_input["controllers"]:
            return self.async_abort(reason="no_modules")

        if self._controllers is not None and user_input is not None:
            try:
                controllers = user_input["controllers"]
                _LOGGER.debug(
                    "controllers: %s",
                    controllers,
                )
                if len(controllers) == 0:
                    return self.async_abort(reason="no_modules")

                if len(controllers) > 1:
                    for controller_id in controllers[1 : len(controllers)]:
                        controller = next(
                            obj
                            for obj in self._controllers
                            if obj["controller"].get("id") == int(controller_id)
                        )
                        _LOGGER.debug(
                            "controller_id: %s",
                            controller_id,
                        )
                        _LOGGER.debug("Adding config entry for: %s", controller)

                        await self.hass.config_entries.async_add(
                            self._create_config_entry(controller=controller)
                        )
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

            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

    async def _async_init_controller(self, user_input: dict[str, str]) -> FlowResult:
        """Handle the initialization of the integration via the cloud API."""
        _LOGGER.debug("🚀 ~ _async_init_controllers:user_input: %s", user_input)
        # await self._async_set_unique_id(user_input)
        # self._abort_if_unique_id_configured()
        return await self._async_finish_controller(user_input)

    # async def _async_set_unique_id(self, unique_id: str) -> None:
    #     """Set the unique ID of the config flow and abort if it already exists."""
    #     await self.async_set_unique_id(unique_id)
    #     self._abort_if_unique_id_configured()

    async def async_step_select_controllers(
        self,
        user_input: dict[str, str] | None = None,
        # validated_input: dict[str, str] | None = None,
    ) -> FlowResult:
        """Handle the selection of controllers."""
        _LOGGER.debug("🚀 ~ async_step_select_controllers:user_input: %s", user_input)
        # _LOGGER.debug(
        #     "🚀 ~ async_step_select_controllers:validated_input: %s", validated_input
        # )
        if not user_input:
            self._controllers = self._create_controllers_array(
                validated_input=self._init_info
            )

            _LOGGER.debug(
                "🚀 ~ async_step_select_controllers:controllers: %s", self._controllers
            )
            data_schema = controllers_schema(controllers=self._controllers)
            _LOGGER.debug(
                "🚀 ~ async_step_select_controllers:data_schema: %s", data_schema
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
                _LOGGER.debug("Context: %s", str(self.context))
                info = await validate_input(self.hass, user_input)
                _LOGGER.debug("Info: %s", info)
                # controllers_names = ""
                # for controller in info["controllers"]:
                #     controllers_names += controller["version"] + " "
                # _LOGGER.debug("Controller names: %s", controllers_names)
                # controllers = self._create_controllers_array(validated_input=info)
                # _LOGGER.debug("Controllers: %s", controllers)

                # await self.async_set_unique_id(user_input[CONF_USERNAME])
                # self._abort_if_unique_id_configured()

                # if len(controllers) == 0:
                #     return self.async_abort(reason="no_modules")

                # if len(controllers) > 1:
                #     for controller in controllers[1 : len(controllers)]:
                #         _LOGGER.debug("Adding config entry for: %s", controller.name)
                #         await self.hass.config_entries.async_add(
                #             self._create_config_entry(controller=controller)
                #         )

                # Store info to use in next step
                self._init_info = info

                return await self.async_step_select_controllers()
                # return self.async_create_entry(
                #     title=controllers[0]["version"], data=controllers[0]
                # )
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

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)

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


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Tech Sterowniki."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "show_things",
                        default=self.config_entry.options.get("show_things"),
                    ): bool
                }
            ),
        )


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(exceptions.HomeAssistantError):
    """Error to indicate there is invalid auth."""
