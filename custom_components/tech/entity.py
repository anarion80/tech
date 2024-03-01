"""TileEntity."""
from abc import abstractmethod
import logging

from homeassistant.helpers import entity

from . import assets
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class TileEntity(entity.Entity):
    """Representation of a TileEntity."""

    def __init__(self, device, api, controller_uid):
        """Initialize the tile entity."""
        self._controller_uid = controller_uid
        self._api = api
        self._id = device["id"]
        self._unique_id = controller_uid + "_" + str(device["id"])
        self._model = device["params"].get("description")
        self._state = self.get_state(device)
        txt_id = device["params"].get("txtId")
        if txt_id:
            self._name = assets.get_text(txt_id)
        else:
            self._name = assets.get_text_by_type(device["type"])

    @property
    def device_info(self):
        """Get device info."""
        return {
            "identifiers": {(DOMAIN, self.unique_id)},
            "name": self.name,
            "manufacturer": "TechControllers",
            "model": self._model,
        }

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return self._unique_id

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @abstractmethod
    def get_state(self, device):
        """Get device state."""
        raise NotImplementedError("Must override get_state")

    def update_properties(self, device):
        """Update the properties of the device based on the provided device information.

        Args:
        device: dict, the device information containing description, zone, setTemperature, and currentTemperature

        Returns:
        None

        """
        # Update _state property
        self._state = self.get_state(device)

    async def async_update(self):
        """Update the state of the entity."""

        device = await self._api.get_tile(self._controller_uid, self._id)
        self.update_properties(device)
