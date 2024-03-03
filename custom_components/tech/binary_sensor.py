"""Platform for binary sensor integration."""
import logging

from homeassistant.components import binary_sensor
from homeassistant.const import CONF_PARAMS, CONF_TYPE, STATE_OFF, STATE_ON

from . import TechCoordinator, assets
from .const import (
    CONTROLLER,
    DOMAIN,
    TYPE_ADDITIONAL_PUMP,
    TYPE_FIRE_SENSOR,
    TYPE_RELAY,
    UDID,
    VISIBILITY,
)
from .entity import TileEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up entry."""
    _LOGGER.debug("Setting up entry for sensors...")
    controller = config_entry.data[CONTROLLER]
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    entities = []
    # for controller in controllers:
    controller_udid = controller[UDID]
    tiles = await coordinator.api.get_module_tiles(controller_udid)
    _LOGGER.debug("Setting up entry for binary sensors...tiles: %s", tiles)
    for t in tiles:
        tile = tiles[t]
        if tile[VISIBILITY] is False:
            continue
        if tile[CONF_TYPE] == TYPE_RELAY:
            entities.append(RelaySensor(tile, coordinator, controller_udid))
        if tile[CONF_TYPE] == TYPE_FIRE_SENSOR:
            entities.append(
                RelaySensor(
                    tile,
                    coordinator,
                    controller_udid,
                    binary_sensor.DEVICE_CLASS_MOTION,
                )
            )
        if tile[CONF_TYPE] == TYPE_ADDITIONAL_PUMP:
            entities.append(RelaySensor(tile, coordinator, controller_udid))

    async_add_entities(entities, True)


class TileBinarySensor(TileEntity, binary_sensor.BinarySensorEntity):
    """Representation of a TileBinarySensor."""

    def get_state(self, device):
        """Get the state of the device."""

    @property
    def state(self):
        """Get the state of the binary sensor."""
        return STATE_ON if self._state else STATE_OFF


class RelaySensor(TileBinarySensor):
    """Representation of a RelaySensor."""

    def __init__(
        self, device, coordinator: TechCoordinator, controller_udid, device_class=None
    ):
        """Initialize the tile relay sensor."""
        TileBinarySensor.__init__(self, device, coordinator, controller_udid)
        self._attr_device_class = device_class
        self._coordinator = coordinator
        icon_id = device[CONF_PARAMS].get("iconId")
        if icon_id:
            self._attr_icon = assets.get_icon(icon_id)
        else:
            self._attr_icon = assets.get_icon_by_type(device[CONF_TYPE])

    def get_state(self, device):
        """Get device state."""
        return device[CONF_PARAMS]["workingStatus"]
