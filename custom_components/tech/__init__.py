"""The Tech Controllers integration."""
import asyncio
import logging

from aiohttp import ClientSession

from homeassistant.components import automation
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_DESCRIPTION, CONF_NAME, CONF_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers import (
    config_validation as cv,
    device_registry as dr,
    entity_registry as er,
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.issue_registry import IssueSeverity, async_create_issue
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from . import assets
from .const import (
    API_TIMEOUT,
    CONTROLLER,
    DOMAIN,
    MANUFACTURER,
    PLATFORMS,
    SCAN_INTERVAL,
    UDID,
    USER_ID,
    VER,
)
from .tech import Tech, TechError, TechLoginError

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


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


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Migrate old entry."""
    _LOGGER.debug("Migrating from version %s", config_entry.version)
    _LOGGER.debug("async_migrate_entry, controller: %s", config_entry)

    device_registry = dr.async_get(hass)
    entity_registry = er.async_get(hass)
    udid = config_entry.data[UDID]

    if config_entry.version == 1:
        # Add controller information to config entry.
        # Update unique_id
        version = 2

        http_session = async_get_clientsession(hass)
        api = Tech(
            http_session, config_entry.data[USER_ID], config_entry.data[CONF_TOKEN]
        )
        controllers = await api.list_modules()
        _LOGGER.debug("async_migrate_entry, controllers: %s", controllers)
        controller = next(obj for obj in controllers if obj.get(UDID) == udid)
        _LOGGER.debug("async_migrate_entry, controller: %s", controller)
        api.modules.setdefault(udid, {"last_update": None, "zones": {}, "tiles": {}})

        zones = await api.get_module_zones(udid)

        data = {
            USER_ID: api.user_id,
            CONF_TOKEN: api.token,
            CONTROLLER: controller,
            VER: controller[VER] + ": " + controller[CONF_NAME],
        }

        # Store the existing entity entries:
        old_entity_entries: dict[str, er.RegistryEntry] = {
            entry.unique_id: entry
            for entry in er.async_entries_for_config_entry(
                entity_registry, config_entry.entry_id
            )
        }
        _LOGGER.debug("async_migrate_entry, old_entity_entries: %s", old_entity_entries)

        # Update config entry
        hass.config_entries.async_update_entry(
            config_entry,
            data=data,
            title=controller[CONF_NAME],
            unique_id=udid,
            version=version,
        )

        # Create new devices as version 1 did not have any:
        for z in zones:
            zone = zones[z]
            device_registry.async_get_or_create(
                config_entry_id=config_entry.entry_id,
                identifiers={(DOMAIN, zone[CONF_DESCRIPTION][CONF_NAME])},
                manufacturer=MANUFACTURER,
                name=zone[CONF_DESCRIPTION][CONF_NAME],
                model=controller[CONF_NAME] + ": " + controller[VER],
                # sw_version= #TODO
                # hw_version= #TODO
            )

        # Update all entities and link them to appropriate devices
        # plus update unique_id, everything else as it was
        for new_entity_entry in er.async_entries_for_config_entry(
            entity_registry, config_entry.entry_id
        ):
            _LOGGER.debug(
                "async_entries_for_original_name, new_entity_entry: %s",
                new_entity_entry,
            )
            if old_entity_entry := old_entity_entries.get(new_entity_entry.unique_id):
                if old_entity_entry.original_name != "":
                    devices = [
                        device
                        for device in device_registry.devices.values()
                        if config_entry.entry_id in device.config_entries
                        and old_entity_entry.original_name in device.name
                    ]
                    _LOGGER.debug(
                        "async_entries_for_original_name, devices: %s", devices
                    )
                    if devices:
                        device = next(
                            obj
                            for obj in devices
                            if obj.identifiers
                            == {(DOMAIN, old_entity_entry.original_name)}
                        )
                        _LOGGER.debug(
                            "async_entries_for_original_name, device: %s", device
                        )
                        if device.name == old_entity_entry.original_name:
                            entity_registry.async_update_entity(
                                old_entity_entry.entity_id,
                                area_id=old_entity_entry.area_id,
                                device_class=old_entity_entry.device_class,
                                device_id=device.id,
                                disabled_by=old_entity_entry.disabled_by,
                                hidden_by=old_entity_entry.hidden_by,
                                icon=old_entity_entry.icon,
                                name=old_entity_entry.name,
                                new_entity_id=old_entity_entry.entity_id,
                                new_unique_id=udid
                                + "_"
                                + str(old_entity_entry.unique_id),
                                unit_of_measurement=old_entity_entry.unit_of_measurement,
                            )

        # for i in old_entity_entries:
        #     old_entity = old_entity_entries.get(i)
        #     _LOGGER.debug("async_entries_for_original_name, old_entity: %s", old_entity)
        #     devices = async_entries_for_original_name(
        #         config_entry, old_entity.original_name
        #     )
        #     _LOGGER.debug("async_entries_for_original_name, devices: %s", devices)

        #     if old_entity_entry := old_entity_entries.get(i):
        #         entity_registry.async_update_entity(
        #             old_entity_entry.entity_id,
        #             area_id=old_entity_entry.area_id,
        #             device_class=old_entity_entry.device_class,
        #             device_id=devices[0]["id"],
        #             disabled_by=old_entity_entry.disabled_by,
        #             hidden_by=old_entity_entry.hidden_by,
        #             icon=old_entity_entry.icon,
        #             name=old_entity_entry.name,
        #             new_entity_id=old_entity_entry.entity_id,
        #             new_unique_id=udid + "_" + str(i),
        #             unit_of_measurement=old_entity_entry.unit_of_measurement,
        #         )

        # After the migration has occurred, grab the new config and device entries
        # new_config_entry = next(
        #     entry
        #     for entry in hass.config_entries.async_entries(DOMAIN)
        #     if entry.data[CONTROLLER][UDID] == udid
        # )
        # _LOGGER.debug("async_migrate_entry, new_config_entry: %s", new_config_entry)
        # _LOGGER.debug(
        #     "async_migrate_entry, async_entries_for_config_entry : %s",
        #     dr.async_entries_for_config_entry(
        #         device_registry, new_config_entry.entry_id
        #     ),
        # )

        # new_entity_entries: dict[str, er.RegistryEntry] = {
        #     entry.unique_id: entry.entity_id
        #     for entry in er.async_entries_for_config_entry(
        #         entity_registry, config_entry.entry_id
        #     )
        # }
        # _LOGGER.debug("async_migrate_entry, new_entity_entries: %s", new_entity_entries)

        # new_device_entry = next(
        #     entry
        #     for entry in dr.async_entries_for_config_entry(
        #         device_registry, new_config_entry.entry_id
        #     )
        # )
        # _LOGGER.debug("async_migrate_entry, new_device_entry: %s", new_device_entry)

        # Update the new entity entries with any customizations from the old ones:
        # for new_entity_entry in er.async_entries_for_device(
        #     entity_registry, new_device_entry.id, include_disabled_entities=True
        # ):
        #     if old_entity_entry := old_entity_entries.get(new_entity_entry.unique_id):
        #         entity_registry.async_update_entity(
        #             new_entity_entry.entity_id,
        #             area_id=old_entity_entry.area_id,
        #             device_class=old_entity_entry.device_class,
        #             disabled_by=old_entity_entry.disabled_by,
        #             hidden_by=old_entity_entry.hidden_by,
        #             icon=old_entity_entry.icon,
        #             name=old_entity_entry.name,
        #             new_entity_id=old_entity_entry.entity_id,
        #             unit_of_measurement=old_entity_entry.unit_of_measurement,
        #         )

        # If any automations are using the old device ID, create a Repairs issues
        # with instructions on how to update it:
        # for new_entity_entry in er.async_entries_for_config_entry(
        #     entity_registry, config_entry.entry_id
        # ):
        #     if entity_automations := automation.automations_with_entity(
        #         hass, new_entity_entry.id
        #     ):
        #         async_create_issue(
        #             hass,
        #             DOMAIN,
        #             f"tech_migration_{config_entry.entry_id}",
        #             is_fixable=False,
        #             is_persistent=True,
        #             severity=IssueSeverity.WARNING,
        #             translation_key="airvisual_pro_migration",
        #             translation_placeholders={
        #                 "udid": udid,
        #                 "new_device_id": new_entity_entry.id,
        #                 "device_automations_string": ", ".join(
        #                     f"`{automation}`" for automation in entity_automations
        #                 ),
        #             },
        #         )

        _LOGGER.debug("Migration to version %s successful", version)

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
