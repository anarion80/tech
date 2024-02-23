"""Support for Tech HVAC system."""
import itertools
import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities
) -> None:
    """Set up entry."""
    _LOGGER.debug(
        "Setting up sensor entry, module udid: %s", config_entry.data["module"]["udid"]
    )
    api = hass.data[DOMAIN][config_entry.entry_id]
    zones = await api.get_module_zones(config_entry.data["module"]["udid"])
    tiles = await api.get_module_tiles(config_entry.data["module"]["udid"])

    battery_devices = map_to_battery_sensors(zones, api, config_entry)
    temperature_sensors = map_to_temperature_sensors(zones, api, config_entry)
    humidity_sensors = map_to_humidity_sensors(zones, api, config_entry)
    tile_sensors = map_to_tile_sensors(tiles, api, config_entry)

    async_add_entities(
        itertools.chain(
            battery_devices, temperature_sensors, humidity_sensors, tile_sensors
        ),
        True,
    )


def map_to_battery_sensors(zones, api, config_entry):
    """Map the battery-operating devices in the zones to TechBatterySensor objects.

    Args:
    zones: list of devices
    api: the api object
    config_entry: the config entry object

    Returns:
    - list of TechBatterySensor objects

    """
    devices = filter(
        lambda deviceIndex: is_battery_operating_device(zones[deviceIndex]), zones
    )
    return (
        TechBatterySensor(zones[deviceIndex], api, config_entry)
        for deviceIndex in devices
    )


def is_battery_operating_device(device) -> bool:
    """Check if the device is operating on battery.

    Args:
    device: dict - The device information.

    Returns:
    bool - True if the device is operating on battery, False otherwise.

    """
    return device["zone"]["batteryLevel"] is not None


def map_to_temperature_sensors(zones, api, config_entry):
    """Map the zones to temperature sensors using the provided API and config entry.

    Args:
    zones (list): List of zones
    api (object): The API object
    config_entry (object): The config entry object

    Returns:
    list: List of TechTemperatureSensor objects

    """
    devices = filter(
        lambda deviceIndex: is_temperature_operating_device(zones[deviceIndex]), zones
    )
    return (
        TechTemperatureSensor(zones[deviceIndex], api, config_entry)
        for deviceIndex in devices
    )


def is_temperature_operating_device(device) -> bool:
    """Check if the device's current temperature is available.

    Args:
        device (dict): The device information.

    Returns:
        bool: True if the current temperature is available, False otherwise.

    """
    return device["zone"]["currentTemperature"] is not None


def map_to_humidity_sensors(zones, api, config_entry):
    """Map zones to humidity sensors.

    Args:
    zones: list of zones
    api: API to interact with humidity sensors
    config_entry: configuration entry for the sensors

    Returns:
    list of TechHumiditySensor instances

    """
    # Filter devices that are humidity operating devices
    devices = filter(
        lambda deviceIndex: is_humidity_operating_device(zones[deviceIndex]), zones
    )
    # Map devices to TechHumiditySensor instances
    return (
        TechHumiditySensor(zones[deviceIndex], api, config_entry)
        for deviceIndex in devices
    )


def is_humidity_operating_device(device) -> bool:
    """Check if the device is operating based on the humidity level in its zone.

    Args:
    device: dict - The device information containing the zone and humidity level.

    Returns:
    bool - True if the device is operating based on the humidity level, False otherwise.

    """
    return device["zone"]["humidity"] is not None and device["zone"]["humidity"] != 0


def map_to_tile_sensors(tiles, api, config_entry):
    """Map tiles to corresponding sensor objects based on the device type and create a list of sensor objects.

    Args:
    tiles: List of tiles
    api: API object
    config_entry: Configuration entry object

    Returns:
    List of sensor objects

    """
    # Filter devices with outside temperature
    devices_outside_temperature = filter(
        lambda deviceIndex: is_outside_temperature_tile(tiles[deviceIndex]), tiles
    )

    # Create sensor objects for devices with outside temperature
    devices_objects = (
        TechOutsideTempTile(tiles[deviceIndex], api, config_entry)
        for deviceIndex in devices_outside_temperature
    )

    return devices_objects


def is_outside_temperature_tile(device) -> bool:
    """Check if the device is a temperature sensor.

    Args:
    device (dict): The device information.

    Returns:
    bool: True if the device is a temperature sensor, False otherwise.

    """
    return device["params"]["description"] == "Temperature sensor"


class TechBatterySensor(SensorEntity):
    """Representation of a Tech battery sensor."""

    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, device, api, config_entry):
        """Initialize the Tech battery sensor."""
        _LOGGER.debug("Init TechBatterySensor... ")
        self._config_entry = config_entry
        self._api = api
        self._id = device["zone"]["id"]
        self.update_properties(device)

    def update_properties(self, device):
        """Update properties from the TechBatterySensor object.

        Args:
        device: dict, the device data containing information about the device

        Returns:
        None

        """
        self._name = device["description"]["name"]
        self._attr_native_value = device["zone"]["batteryLevel"]

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return f"climate_{self._id}_battery"

    @property
    def name(self):
        """Return the name of the device."""
        return f"{self._name} battery"

    async def async_update(self):
        """Call by the Tech device callback to update state."""
        _LOGGER.debug(
            "Updating Tech battery sensor: %s, udid: %s, id: %s",
            self._name,
            self._config_entry.data["module"]["udid"],
            self._id,
        )
        device = await self._api.get_zone(
            self._config_entry.data["module"]["udid"], self._id
        )
        self.update_properties(device)


class TechTemperatureSensor(SensorEntity):
    """Representation of a Tech temperature sensor."""

    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, device, api, config_entry):
        """Initialize the Tech temperature sensor."""
        _LOGGER.debug("Init TechTemperatureSensor... ")
        self._config_entry = config_entry
        self._api = api
        self._id = device["zone"]["id"]
        self.update_properties(device)

    def update_properties(self, device):
        """Update the properties of the TechTemperatureSensor object.

        Args:
        device: dict, the device data containing information about the device

        Returns:
        None

        """
        # Set the name of the device
        self._name = device["description"]["name"]

        # Check if the current temperature is available, and update the native value accordingly
        if device["zone"]["currentTemperature"] is not None:
            self._attr_native_value = device["zone"]["currentTemperature"] / 10
        else:
            self._attr_native_value = None

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return f"climate_{self._id}_temperature"

    @property
    def name(self):
        """Return the name of the device."""
        return f"{self._name} temperature"

    async def async_update(self):
        """Call by the Tech device callback to update state."""
        _LOGGER.debug(
            "Updating Tech temp. sensor: %s, udid: %s, id: %s",
            self._name,
            self._config_entry.data["module"]["udid"],
            self._id,
        )
        device = await self._api.get_zone(
            self._config_entry.data["module"]["udid"], self._id
        )
        self.update_properties(device)


class TechOutsideTempTile(SensorEntity):
    """Representation of a Tech outside temperature tile sensor."""

    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, device, api, config_entry):
        """Initialize the Tech temperature sensor."""
        _LOGGER.debug("Init TechOutsideTemperatureTile... ")
        self._config_entry = config_entry
        self._api = api
        self._id = device["id"]
        self.update_properties(device)
        _LOGGER.debug(
            "Init TechOutsideTemperatureTile...: %s, udid: %s, id: %s",
            self._name,
            self._config_entry.data["module"]["udid"],
            self._id,
        )

    def update_properties(self, device):
        """Update the properties of the TechOutsideTempTile object.

        Args:
        device: dict containing information about the device

        Returns:
        None

        """
        # Set the name based on the device id
        self._name = "outside_" + str(device["id"])

        if device["params"]["value"] is not None:
            # Update the native value based on the device params
            self._attr_native_value = device["params"]["value"] / 10
        else:
            # Set native value to None if device params value is None
            self._attr_native_value = None

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return f"climate_{self._id}_out_temperature"

    @property
    def name(self):
        """Return the name of the device."""
        return f"{self._name} temperature"

    async def async_update(self):
        """Call by the Tech device callback to update state."""
        _LOGGER.debug(
            "Updating Tech outs. temp. tile sensor: %s, udid: %s, id: %s",
            self._name,
            self._config_entry.data["module"]["udid"],
            self._id,
        )
        device = await self._api.get_tile(
            self._config_entry.data["module"]["udid"], self._id
        )
        self.update_properties(device)


class TechHumiditySensor(SensorEntity):
    """Representation of a Tech humidity sensor."""

    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, device, api, config_entry):
        """Initialize the Tech humidity sensor."""
        _LOGGER.debug("Init TechHumiditySensor... ")
        self._config_entry = config_entry
        self._api = api
        self._id = device["zone"]["id"]
        self.update_properties(device)

    def update_properties(self, device):
        """Update the properties of the TechHumiditySensor object.

        Args:
        device (dict): The device information.

        Returns:
        None

        """
        # Update the name of the device
        self._name = device["description"]["name"]

        # Check if the humidity value is not zero and update the native value attribute accordingly
        if device["zone"]["humidity"] != 0:
            self._attr_native_value = device["zone"]["humidity"]
        else:
            self._attr_native_value = None

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return f"climate_{self._id}_humidity"

    @property
    def name(self):
        """Return the name of the device."""
        return f"{self._name} humidity"

    async def async_update(self):
        """Call by the Tech device callback to update state."""
        _LOGGER.debug(
            "Updating Tech hum. sensor: %s, udid: %s, id: %s",
            self._name,
            self._config_entry.data["module"]["udid"],
            self._id,
        )
        device = await self._api.get_zone(
            self._config_entry.data["module"]["udid"], self._id
        )
        self.update_properties(device)
