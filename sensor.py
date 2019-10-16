"""
Provides a sensor to track Opel OnStar information
"""
import logging
import asyncio
from datetime import timedelta
from onstar import onstar

import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
import homeassistant.helpers.config_validation as cv
from homeassistant.const import (
    CONF_NAME, CONF_USERNAME, CONF_PASSWORD, CONF_PIN,
    CONF_SCAN_INTERVAL, CONF_RESOURCES, CONF_ALIAS, ATTR_STATE, STATE_UNKNOWN)
from homeassistant.exceptions import PlatformNotReady
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = 'Opel Onstar'

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=300)

SENSOR_TYPES = {
    'onstar.plate': ['Plate', '', 'mdi:account-card-details'],
    'onstar.laststatus': ['Last updated', '', 'mdi:update'],
    'onstar.warningcount': ['Warnings', '', 'mdi:account-alert'],
    'onstar.errorcount': ['Errors', '', 'mdi:alert-circle'],
    'onstar.oillife': ['Oil life', '%', 'mdi:oil'],
    'onstar.fuellevel': ['Fuel level', '%', 'mdi:gas-station'],
    'onstar.ignition': ['Ignition', '', 'mdi:power-standby'],
    'onstar.odometer': ['Odometer', 'km', 'mdi:gauge'],
    'onstar.tirelf': ['Left Front Tyre', 'kPa', 'mdi:car'],
    'onstar.tirelr': ['Left Rear Tyre', 'kPa', 'mdi:car-back'],
    'onstar.tirerf': ['Right Front Tyre', 'kPa', 'mdi:car'],
    'onstar.tirerr': ['Right Rear Tyre', 'kPa', 'mdi:car-back'],
    'onstar.tirestatuslf': ['Left Front Tyre Status', None, None],
    'onstar.tirestatuslr': ['Left Rear Tyre Status', None, None],
    'onstar.tirestatusrf': ['Right Front Tyre Status', None, None],
    'onstar.tirestatusrr': ['Right Rear Tyre Status', None, None],
    'onstar.nextmainodo': ['Next maintenance', None, None],
    'onstar.nextmaindate': ['Next maintenance Date', None, None],
    'onstar.airbagok': ['Airbag status', None, None],
}


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Required(CONF_USERNAME): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
    vol.Required(CONF_PIN): cv.string,
    vol.Optional(CONF_PASSWORD): cv.string,
    vol.Required(CONF_RESOURCES):
        vol.All(cv.ensure_list, [vol.In(SENSOR_TYPES)]),
})


def setup_platform(hass, config, add_entities, discovery_info=None):
    name = config.get(CONF_NAME)

    username = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)
    pin = config.get(CONF_PIN)

    data = OnStarData(username, password,pin)

    if data.status is None:
        _LOGGER.error("No data received from OnStar, unable to setup")
        raise PlatformNotReady

    _LOGGER.debug('OnStar sensors available: %s', data.status)

    entities = []

    for resource in config[CONF_RESOURCES]:
        sensor_type = resource.lower()

        if sensor_type in data.status:
            entities.append(OnStarSensor(name, data, sensor_type))
        else:
            _LOGGER.warning(
                "Sensor type: %s does not appear in OnStar status "
                "output, cannot add", sensor_type)

    data.update(no_throttle=True)
    add_entities(entities, True)


class OnStarSensor(Entity):
    """Representation of a sensor entity for OnStar status values."""

    def __init__(self, name, data, sensor_type):
        """Initialize the sensor."""
        self._data = data
        self.type = sensor_type
        #self._name = "{} {}".format(name, SENSOR_TYPES[sensor_type][0])
        self._name = SENSOR_TYPES[sensor_type][0]
        self.entity_id= "sensor.{}".format(sensor_type.replace('.','_'))
        self._unit = SENSOR_TYPES[sensor_type][1]
        self._state = None

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
        return SENSOR_TYPES[self.type][2]

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
        if self._data.status is None:
            self._state = None
            return

        if self.type not in self._data.status:
            self._state = None
        else:
            self._state = self._data.status[self.type]


class OnStarData(object):
    """Stores the data retrieved from OnStar.
    For each entity to use, acts as the single point responsible for fetching
    updates from the server.
    """

    def __init__(self, username, password, pin):
        """Initialize the data object."""
        self._username = username
        self._password = password
        self._pin = pin

        self._status = None

    @property
    def status(self):
        """Get latest update if throttle allows. Return status."""
        self.update()
        return self._status

    # Retrieves info from OnStar
    def _get_status(self):

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            o = onstar.OnStar(self._username, self._password, self._pin, loop)
            loop.run_until_complete(o.refresh())

            v={}
            v["onstar.plate"]=o.get_diagnostics().results[0].vehicle.licensePlate
            v["onstar.laststatus"]=o.get_diagnostics().results[0].updatedOn
            v["onstar.warningcount"]=o.get_diagnostics().results[0].warningCount
            v["onstar.errorcount"]=o.get_diagnostics().results[0].errorCount
            v["onstar.oillife"]=round(o.get_diagnostics().results[0].reportData.metrics.oilLife*100,1)
            v["onstar.fuellevel"]=int(round(o.get_diagnostics().results[0].reportData.metrics.fuelLevel*100))
            v["onstar.ignition"]=o.get_diagnostics().results[0].reportData.metrics.ignition
            v["onstar.odometer"]=int(round(o.get_diagnostics().results[0].reportData.metrics.odometer))
            v["onstar.tirelf"]=o.get_diagnostics().results[0].reportData.metrics.tirePressureLf
            v["onstar.tirelr"]=o.get_diagnostics().results[0].reportData.metrics.tirePressureLr
            v["onstar.tirerf"]=o.get_diagnostics().results[0].reportData.metrics.tirePressureRf
            v["onstar.tirerr"]=o.get_diagnostics().results[0].reportData.metrics.tirePressureRr
            v["onstar.tirestatuslf"]=o.get_diagnostics().results[0].reportData.metrics.tireStatusLf=="GREEN"
            v["onstar.tirestatuslr"]=o.get_diagnostics().results[0].reportData.metrics.tireStatusLr=="GREEN"
            v["onstar.tirestatusrf"]=o.get_diagnostics().results[0].reportData.metrics.tireStatusRf=="GREEN"
            v["onstar.tirestatusrr"]=o.get_diagnostics().results[0].reportData.metrics.tireStatusRr=="GREEN"
            v["onstar.nextmaindate"]=o.get_diagnostics().results[0].reportData.maintenance.nextMaintDate
            v["onstar.nextmainodo"]=o.get_diagnostics().results[0].reportData.maintenance.nextMaintOdometer
            v["onstar.airbagok"]=o.get_diagnostics().results[0].reportData.sections.airbag.status=="GREEN"
            
            return v
        except (ConnectionResetError) as err:
            _LOGGER.debug(
                "Error getting OnStar info: %s", err)
            return None

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self, **kwargs):
        """Fetch the latest status from OnStar."""
        self._status = self._get_status()
