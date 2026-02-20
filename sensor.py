"""
Provides a sensor to track Opel OnStar information.
"""
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.exceptions import PlatformNotReady

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the OnStar sensor platform."""
    data = hass.data[DOMAIN]

    if data.status is None:
        _LOGGER.error("No data received from OnStar, unable to setup")
        raise PlatformNotReady

    _LOGGER.info("OnStar sensors available: %s", data.status)

    entities = []

    for resource in data.status:
        if resource in data.SENSOR_TYPES:
            entities.append(OnStarSensor(data, resource))
        else:
            _LOGGER.warning(
                "Sensor type: %s does not appear in OnStar sensor types, "
                "cannot add",
                resource,
            )

    data.update(no_throttle=True)
    add_entities(entities, True)


class OnStarSensor(SensorEntity):
    """Representation of a sensor entity for OnStar status values."""

    def __init__(self, data, sensor_type):
        """Initialize the sensor."""
        self._data = data
        self.type = sensor_type

        sensor_info = self._data.SENSOR_TYPES[sensor_type]
        self._attr_name = sensor_info[0]
        self._attr_unique_id = f"onstar_{sensor_type.replace('.', '_')}"
        self._attr_native_unit_of_measurement = sensor_info[1]
        self._attr_icon = sensor_info[2]
        self._state = None

    @property
    def should_poll(self):
        """Return the polling state."""
        return True

    @property
    def native_value(self):
        """Return entity state."""
        return self._state

    @property
    def extra_state_attributes(self):
        """Return the sensor attributes."""
        return {"state": self.display_state()}

    def display_state(self):
        """Return display state."""
        if self._data.status is None:
            return "OFF"
        return "ON"

    def update(self):
        """Get the latest status and use it to update our sensor state."""
        _LOGGER.debug("Update state")
        if self._data.status is None:
            self._state = None
            return

        if self.type not in self._data.status:
            self._state = None
        else:
            self._state = self._data.status[self.type]

    @property
    def force_update(self):
        """Return True if state updates should be forced."""
        return False
