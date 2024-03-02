"""Platform for binary sensor integration."""
import logging

from homeassistant.components import binary_sensor
from homeassistant.const import CONF_PARAMS, CONF_TYPE, STATE_OFF, STATE_ON

from . import assets
from .const import (
    CONTROLLER,
    DOMAIN,
    TILES,
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
    api = hass.data[DOMAIN][config_entry.entry_id]
    controller = config_entry.data[CONTROLLER]

    entities = []
    # for controller in controllers:
    controller_udid = controller[UDID]
    data = await api.module_data(controller_udid)
    tiles = data[TILES]
    for t in tiles:
        tile = tiles[t]
        if tile[VISIBILITY] is False:
            continue
        if tile[CONF_TYPE] == TYPE_RELAY:
            entities.append(RelaySensor(tile, api, controller_udid))
        if tile[CONF_TYPE] == TYPE_FIRE_SENSOR:
            entities.append(
                RelaySensor(
                    tile, api, controller_udid, binary_sensor.DEVICE_CLASS_MOTION
                )
            )
        if tile[CONF_TYPE] == TYPE_ADDITIONAL_PUMP:
            entities.append(RelaySensor(tile, api, controller_udid))

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

    def __init__(self, device, api, controller_udid, device_class=None):
        """Initialize the tile relay sensor."""
        TileBinarySensor.__init__(self, device, api, controller_udid)
        self._attr_device_class = device_class
        icon_id = device[CONF_PARAMS].get("iconId")
        if icon_id:
            self._attr_icon = assets.get_icon(icon_id)
        else:
            self._attr_icon = assets.get_icon_by_type(device[CONF_TYPE])

    def get_state(self, device):
        """Get device state."""
        return device[CONF_PARAMS]["workingStatus"]
