"""Support for Tech HVAC system."""
import logging
from typing import Optional

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SUPPORT_HVAC = [HVACMode.HEAT, HVACMode.OFF]


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up entry."""
    udid = config_entry.data["controller"]["udid"]
    _LOGGER.debug("Setting up entry, controller udid: %s", udid)
    model = (
        config_entry.data["controller"]["name"]
        + ": "
        + config_entry.data["controller"]["version"]
    )
    api = hass.data[DOMAIN][config_entry.entry_id]
    zones = await api.get_module_zones(udid)
    _LOGGER.debug("👴 Zones via get_module_zones: %s", zones)
    thermostats = [TechThermostat(zones[zone], api, udid, model) for zone in zones]

    async_add_entities(thermostats, True)


class TechThermostat(ClimateEntity):
    """Representation of a Tech climate."""

    def __init__(self, device, api, udid, model):
        """Initialize the Tech device."""
        _LOGGER.debug("Init TechThermostat...")
        self._udid = udid
        self._api = api
        self._id = device["zone"]["id"]
        self._unique_id = udid + "_" + str(device["zone"]["id"])
        self.device_name = device["description"]["name"]
        # self.device_name = "Climate controller"
        self.manufacturer = "TechControllers"
        self.model = model
        self._temperature = None
        self.update_properties(device)
        # Remove the line below after HA 2025.1
        self._enable_turn_on_off_backwards_compatibility = False

    @property
    def device_info(self):
        """Returns device information in a dictionary format."""
        return {
            # "identifiers": {(DOMAIN, "climate")},  # Unique identifiers for the device
            "identifiers": {(DOMAIN, self._id)},  # Unique identifiers for the device
            "name": self.device_name,  # Name of the device
            "model": self.model,  # Model of the device
            "manufacturer": self.manufacturer,  # Manufacturer of the device
        }

    def update_properties(self, device):
        """Update the properties of the HVAC device based on the data from the device.

        Args:
        self (object): instance of the class
        device (dict): The device data containing information about the device's properties.

        Returns:
        None

        """
        # Update device name
        self._name = device["description"]["name"]

        # Update target temperature
        if device["zone"]["setTemperature"] is not None:
            self._target_temperature = device["zone"]["setTemperature"] / 10
        else:
            self._target_temperature = None

        # Update current temperature
        if device["zone"]["currentTemperature"] is not None:
            self._temperature = device["zone"]["currentTemperature"] / 10
        else:
            self._temperature = None

        # Update humidity
        if device["zone"]["humidity"] is not None:
            self._humidity = device["zone"]["humidity"]
        else:
            self._humidity = None

        # Update HVAC state
        state = device["zone"]["flags"]["relayState"]
        hvac_mode = device["zone"]["flags"]["algorithm"]
        if state == "on":
            if hvac_mode == "heating":
                self._state = HVACAction.HEATING
            elif hvac_mode == "cooling":
                self._state = HVACAction.COOLING
        elif state == "off":
            self._state = HVACAction.IDLE
        else:
            self._state = HVACAction.OFF

        # Update HVAC mode
        mode = device["zone"]["zoneState"]
        if mode in ("zoneOn", "noAlarm"):
            self._mode = HVACMode.HEAT
        else:
            self._mode = HVACMode.OFF

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return self._unique_id

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return (
            ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.TURN_ON
            | ClimateEntityFeature.TURN_OFF
        )

    @property
    def hvac_mode(self):
        """Return hvac operation ie. heat, cool mode.

        Need to be one of HVAC_MODE_*.
        """
        return self._mode

    @property
    def hvac_modes(self):
        """Return the list of available hvac operation modes.

        Need to be a subset of HVAC_MODES.
        """
        return SUPPORT_HVAC

    @property
    def hvac_action(self) -> Optional[str]:
        """Return the current running hvac operation if supported.

        Need to be one of CURRENT_HVAC_*.
        """
        return self._state

    async def async_update(self):
        """Call by the Tech device callback to update state."""
        _LOGGER.debug(
            "Updating Tech zone: %s, udid: %s, id: %s", self._name, self._udid, self._id
        )
        device = await self._api.get_zone(self._udid, self._id)
        self.update_properties(device)

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return UnitOfTemperature.CELSIUS

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._temperature

    @property
    def current_humidity(self):
        """Return current humidity."""
        return self._humidity

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._target_temperature

    async def async_set_temperature(self, **kwargs):
        """Set new target temperatures."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature:
            _LOGGER.debug("%s: Setting temperature to %s", self._name, temperature)
            self._temperature = temperature
            await self._api.set_const_temp(self._udid, self._id, temperature)

    async def async_set_hvac_mode(self, hvac_mode):
        """Set new target hvac mode."""
        _LOGGER.debug("%s: Setting hvac mode to %s", self._name, hvac_mode)
        if hvac_mode == HVACMode.OFF:
            await self._api.set_zone(self._udid, self._id, False)
        elif hvac_mode == HVACMode.OFF:
            await self._api.set_zone(self._udid, self._id, True)
