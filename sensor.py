"""
Provides a sensor to track Opel OnStar information
"""
import logging

from . import (DOMAIN)

from homeassistant.const import ATTR_STATE
from homeassistant.exceptions import PlatformNotReady
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import track_utc_time_change

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_entities, discovery_info=None):

    data = hass.data[DOMAIN]

    if data.status is None:
        _LOGGER.error("No data received from OnStar, unable to setup")
        raise PlatformNotReady

    _LOGGER.info('OnStar sensors available: %s', data.status)

    entities = []

    for resource in data.status:
        sensor_type = resource.lower()

        if sensor_type in data.status:
            entities.append(OnStarSensor(data, sensor_type, hass))
        else:
            _LOGGER.warning(
                "Sensor type: %s does not appear in OnStar status "
                "output, cannot add", sensor_type)

    data.update(no_throttle=True)
    add_entities(entities, True)


class OnStarSensor(Entity):
    """Representation of a sensor entity for OnStar status values."""

    def __init__(self, data, sensor_type, hass):
        """Initialize the sensor."""
        self._data = data
        self.type = sensor_type
        self._name = self._data.SENSOR_TYPES[sensor_type][0]
        self.entity_id= "sensor.{}".format(sensor_type.replace('.','_'))
        self._unit = self._data.SENSOR_TYPES[sensor_type][1]
        self._state = None
        self._hass = hass

        self.setup()

    @property
    def name(self):
        return self._name

#    @property
#    def entity_id(self):
#        return self._entity_id

    @property
    def should_poll(self):
        """Return the polling state."""
        return True

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return self._data.SENSOR_TYPES[self.type][2]

    @property
    def state(self):
        """Return entity state """
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return self._unit

    @property
    def device_state_attributes(self):
        """Return the sensor attributes."""
        attr = dict()
        attr[ATTR_STATE] = self.display_state()
        return attr

    def display_state(self):
        """Return display state."""
        if self._data.status is None:
            return 'OFF'
        else:
            return 'ON'

    def update(self):
        """Get the latest status and use it to update our sensor state."""
        _LOGGER.info("Update state")
        if self._data.status is None:
            self._state = None
            return

        if self.type not in self._data.status:
            self._state = None
        else:
            self._state = self._data.status[self.type]

    def force_update(self):
        return False

    def setup(self):
        """Schedule update of state by HA"""
        track_utc_time_change(
            self._hass, lambda now: self.schedule_update_ha_state(True), second=range(0, 60, 45)
        )
