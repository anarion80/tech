"""Support for Tech HVAC system."""
# import itertools
import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import Entity

from . import assets
from .const import (
    DOMAIN,
    TYPE_FAN,
    TYPE_FUEL_SUPPLY,
    TYPE_MIXING_VALVE,
    TYPE_TEMPERATURE,
    TYPE_TEMPERATURE_CH,
    TYPE_TEXT,
    TYPE_VALVE,
)
from .entity import TileEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities
) -> None:
    """Set up entry."""
    _LOGGER.debug(
        "Setting up sensor entry, controller udid: %s",
        config_entry.data["controller"]["udid"],
    )
    api = hass.data[DOMAIN][config_entry.entry_id]
    model = (
        config_entry.data["controller"]["name"]
        + ": "
        + config_entry.data["controller"]["version"]
    )

    controller = config_entry.data["controller"]
    controller_udid = controller["udid"]

    data = await api.module_data(controller_udid)
    zones = data["zones"]
    tiles = data["tiles"]

    entities = []
    for t in tiles:
        tile = tiles[t]
        if tile["visibility"] is False:
            continue
        if tile["type"] == TYPE_TEMPERATURE:
            entities.append(TileTemperatureSensor(tile, api, controller_udid))
        if tile["type"] == TYPE_TEMPERATURE_CH:
            entities.append(TileWidgetSensor(tile, api, controller_udid))
        if tile["type"] == TYPE_FAN:
            entities.append(TileFanSensor(tile, api, controller_udid))
        if tile["type"] == TYPE_VALVE:
            entities.append(TileValveSensor(tile, api, controller_udid))
            # TODO: this class _init_ definition needs to be fixed. See comment below.
            # entities.append(TileValveTemperatureSensor(tile, api, controller_udid, VALVE_SENSOR_RETURN_TEMPERATURE))
            # entities.append(TileValveTemperatureSensor(tile, api, controller_udid, VALVE_SENSOR_SET_TEMPERATURE))
            # entities.append(TileValveTemperatureSensor(tile, api, controller_udid, VALVE_SENSOR_CURRENT_TEMPERATURE))
        if tile["type"] == TYPE_MIXING_VALVE:
            entities.append(TileMixingValveSensor(tile, api, controller_udid))
        if tile["type"] == TYPE_FUEL_SUPPLY:
            entities.append(TileFuelSupplySensor(tile, api, controller_udid))
        if tile["type"] == TYPE_TEXT:
            entities.append(TileTextSensor(tile, api, controller_udid))

    async_add_entities(entities, True)

    async_add_entities(
        [
            ZoneTemperatureSensor(zones[zone], api, controller_udid, model)
            for zone in zones
        ],
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
            self._config_entry.data["controller"]["udid"],
            self._id,
        )
        device = await self._api.get_zone(
            self._config_entry.data["controller"]["udid"], self._id
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
            self._config_entry.data["controller"]["udid"],
            self._id,
        )
        device = await self._api.get_zone(
            self._config_entry.data["controller"]["udid"], self._id
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
            self._config_entry.data["controller"]["udid"],
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
            self._config_entry.data["controller"]["udid"],
            self._id,
        )
        device = await self._api.get_tile(
            self._config_entry.data["controller"]["udid"], self._id
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
            self._config_entry.data["controller"]["udid"],
            self._id,
        )
        device = await self._api.get_zone(
            self._config_entry.data["controller"]["udid"], self._id
        )
        self.update_properties(device)


class ZoneSensor(Entity):
    """Representation of a Zone Sensor."""

    def __init__(self, device, api, controller_udid, model):
        """Initialize the sensor."""
        _LOGGER.debug("Init ZoneSensor...")
        self._controller_udid = controller_udid
        self._api = api
        self._id = device["zone"]["id"]
        self._device_name = device["description"]["name"]
        self._model = model
        self.update_properties(device)

    def update_properties(self, device):
        """Update the properties of the device based on the provided device information.

        Args:
        device: dict, the device information containing description, zone, setTemperature, and currentTemperature

        Returns:
        None

        """
        # Update name property
        self._name = device["description"]["name"]

        # Update target_temperature property
        if device["zone"]["setTemperature"] is not None:
            self._target_temperature = device["zone"]["setTemperature"] / 10
        else:
            self._target_temperature = None

        # Update temperature property
        if device["zone"]["currentTemperature"] is not None:
            self._temperature = device["zone"]["currentTemperature"] / 10
        else:
            self._temperature = None

    @property
    def device_info(self):
        """Get device information.

        Returns:
        dict: A dictionary containing device information.

        """
        # Return device information
        return {
            "identifiers": {(DOMAIN, self.unique_id)},
            "name": self._device_name,
            "manufacturer": "TechControllers",
            "model": self._model,
        }

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return self._id

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._temperature

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return UnitOfTemperature.CELSIUS

    async def async_update(self):
        """Asynchronously updates the device."""
        # Get zone from API
        device = await self._api.get_zone(self._controller_udid, self.unique_id)
        # Update properties
        self.update_properties(device)


class ZoneTemperatureSensor(ZoneSensor):
    """Representation of a Zone Temperature Sensor."""

    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{self._name} Temperature"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._temperature


class TileSensor(TileEntity, Entity):
    """Representation of a TileSensor."""

    def get_state(self, device):
        """Get the state of the device."""


class TileTemperatureSensor(TileSensor):
    """Representation of a Tile Temperature Sensor."""

    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, device, api, controller_udid):
        """Initialize the sensor."""
        TileSensor.__init__(self, device, api, controller_udid)

    def get_state(self, device):
        """Get the state of the device."""
        return device["params"]["value"] / 10


class TileFuelSupplySensor(TileSensor):
    """Representation of a Tile Fuel Supply Sensor."""

    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, device, api, controller_udid):
        """Initialize the sensor."""
        TileSensor.__init__(self, device, api, controller_udid)

    def get_state(self, device):
        """Get the state of the device."""
        return device["params"]["percentage"]


class TileFanSensor(TileSensor):
    """Representation of a Tile Fan Sensor."""

    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, device, api, controller_udid):
        """Initialize the sensor."""
        TileSensor.__init__(self, device, api, controller_udid)
        self._attr_icon = assets.get_icon_by_type(device["type"])

    def get_state(self, device):
        """Get the state of the device."""
        return device["params"]["gear"]


class TileTextSensor(TileSensor):
    """Representation of a Tile Text Sensor."""

    def __init__(self, device, api, controller_udid):
        """Initialize the sensor."""
        TileSensor.__init__(self, device, api, controller_udid)
        self._name = assets.get_text(device["params"]["headerId"])
        self._attr_icon = assets.get_icon(device["params"]["iconId"])

    def get_state(self, device):
        """Get the state of the device."""
        return assets.get_text(device["params"]["statusId"])


class TileWidgetSensor(TileSensor):
    """Representation of a Tile Widget Sensor."""

    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, device, api, controller_udid):
        """Initialize the sensor."""
        TileSensor.__init__(self, device, api, controller_udid)
        self._name = assets.get_text(device["params"]["widget2"]["txtId"])

    def get_state(self, device):
        """Get the state of the device."""
        return device["params"]["widget2"]["value"] / 10


class TileValveSensor(TileSensor):
    """Representation of a Tile Valve Sensor."""

    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, device, api, controller_udid):
        """Initialize the sensor."""
        TileSensor.__init__(self, device, api, controller_udid)
        self._attr_icon = assets.get_icon_by_type(device["type"])
        name = assets.get_text_by_type(device["type"])
        self._name = f"{name} {device['params']['valveNumber']}"

    def get_state(self, device):
        """Get the state of the device."""
        return device["params"]["openingPercentage"]


class TileMixingValveSensor(TileSensor):
    """Representation of a Tile Mixing Valve Sensor."""

    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, device, api, controller_udid):
        """Initialize the sensor."""
        TileSensor.__init__(self, device, api, controller_udid)
        self._attr_icon = assets.get_icon_by_type(device["type"])
        name = assets.get_text_by_type(device["type"])
        self._name = f"{name} {device['params']['valveNumber']}"

    def get_state(self, device):
        """Get the state of the device."""
        return device["params"]["openingPercentage"]


# TODO: this sensor's ID assignment needs to be fixed as base on such ID
#  tech api doesn't return value and we get KeyError
#
# class TileValveTemperatureSensor(TileSensor):
#     def __init__(self, device, api, controller_udid, valve_sensor):
#         self._state_key = valve_sensor["state_key"]
#         sensor_name = assets.get_text(valve_sensor["txt_id"])
#         TileSensor.__init__(self, device, api, controller_udid)
#         self._id = f"{self._id}_{self._state_key}"
#         name = assets.get_text_by_type(device["type"])
#         self._name = f"{name} {device['params']['valveNumber']} {sensor_name}"

#     @property
#     def device_class(self):
#         return sensor.DEVICE_CLASS_TEMPERATURE

#     @property
#     def unit_of_measurement(self):
#         return TEMP_CELSIUS

#     def get_state(self, device):
#         state = device["params"][self._state_key]
#         if state > 100:
#             state = state / 10
#         return state
