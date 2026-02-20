import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.const import (
    CONF_PASSWORD,
    CONF_PIN,
    CONF_USERNAME,
)
from homeassistant.helpers import discovery
from homeassistant.util import Throttle
from onstar.onstar import OnStar

from .const import DOMAIN, MIN_TIME_BETWEEN_UPDATES, ONSTAR_COMPONENTS

_LOGGER = logging.getLogger(__name__)

# DOMAIN moved to const.py

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
            vol.Required(CONF_USERNAME): cv.string,
            vol.Required(CONF_PASSWORD): cv.string,
            vol.Optional(CONF_PIN): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

SERVICE_UPDATE_STATE = "update_state"

# MIN_TIME_BETWEEN_UPDATES and ONSTAR_COMPONENTS moved to const.py

def setup(hass, base_config: dict):
    if base_config is None:
        _LOGGER.error("Base configuration is missing")
        return False
    
    config = base_config.get(DOMAIN)
    if config is None:
        _LOGGER.error("Configuration for %s is missing", DOMAIN)
        return False
    
    username = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)
    pin = config.get(CONF_PIN)
    
    hass.data[DOMAIN] = OnStarData(username, password, pin)
    def _update(call) -> None:
        _LOGGER.info("Update service called")
        hass.data[DOMAIN].update()
    
    hass.services.register(DOMAIN, SERVICE_UPDATE_STATE, _update)

    for component in ONSTAR_COMPONENTS:
        discovery.load_platform(hass, component, DOMAIN, {}, config)

    _LOGGER.info("Done initialization")
    return True


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

        self.gps_position = None
        self._status: dict[str, Any] | None = None

        self.SENSOR_TYPES = {
            'onstar.plate': ['Plate', '', 'mdi:account-card-details'],
            'onstar.laststatus': ['Last updated', '', 'mdi:update'],
            'onstar.warningcount': ['Warnings', '', 'mdi:account-alert'],
            'onstar.errorcount': ['Errors', '', 'mdi:alert-circle'],
            'onstar.oillife': ['Oil life', '%', 'mdi:oil'],
            'onstar.fuellevel': ['Fuel level', '%', 'mdi:gas-station'],
            'onstar.range': ['Fuel range', 'km', 'mdi:gas-station'],
            'onstar.ignition': ['Ignition', '', 'mdi:power-standby'],
            'onstar.odometer': ['Odometer', 'km', 'mdi:gauge'],
            'onstar.tirelf': ['Left Front Tire', 'kPa', 'mdi:car'],
            'onstar.tirelr': ['Left Rear Tire', 'kPa', 'mdi:car-back'],
            'onstar.tirerf': ['Right Front Tire', 'kPa', 'mdi:car'],
            'onstar.tirerr': ['Right Rear Tire', 'kPa', 'mdi:car-back'],
            'onstar.tirestatuslf': ['Left Front Tire Status', None, None],
            'onstar.tirestatuslr': ['Left Rear Tire Status', None, None],
            'onstar.tirestatusrf': ['Right Front Tire Status', None, None],
            'onstar.tirestatusrr': ['Right Rear Tire Status', None, None],
            'onstar.tiresetting': ['Tire setting', None, None],
            'onstar.ftirepressure': ['Front Tires expected pressure', 'kPa', None],
            'onstar.rtirepressure': ['Rear Tire expected pressure', 'kPa', None],
            'onstar.nextmainodo': ['Next maintenance', 'km', None],
            'onstar.nextmaindate': ['Next maintenance Date', None, 'mdi:calendar'],
            'onstar.airbagok': ['Airbag status', None, None],
            'onstar.localization': ['Latest localization', None, 'mdi:compass'],
            'onstar.vin': ['VIN', None, 'mdi:id-card'],
        }

    # Retrieves info from OnStar
    def _get_status(self):

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            o = OnStar(self._username, self._password, self._pin, loop)
            loop.run_until_complete(o.refresh())

            v: dict[str, Any] = {}
            v["onstar.plate"]=o.get_diagnostics().results[0].vehicle.licensePlate
            v["onstar.vin"]=o.get_diagnostics().results[0].vehicle.vehicleVIN
            v["onstar.laststatus"]=self._get_date(o.get_diagnostics().results[0].updatedOn)
            v["onstar.warningcount"]=o.get_diagnostics().results[0].warningCount
            v["onstar.errorcount"]=o.get_diagnostics().results[0].errorCount
            v["onstar.oillife"]=round(o.get_diagnostics().results[0].reportData.metrics.oilLife*100,1)
            v["onstar.fuellevel"]=int(round(o.get_diagnostics().results[0].reportData.metrics.fuelLevel*100))
            v["onstar.range"]=int(round(o.get_diagnostics().results[0].reportData.metrics.fuelRange))
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
            v["onstar.tiresetting"]=o.get_diagnostics().results[0].reportData.metrics.placardSetting
            v["onstar.ftirepressure"]=o.get_diagnostics().results[0].reportData.metrics.placardFront
            v["onstar.rtirepressure"]=o.get_diagnostics().results[0].reportData.metrics.placardRear
            v["onstar.nextmaindate"]=o.get_diagnostics().results[0].reportData.maintenance.nextMaintDate
            v["onstar.nextmainodo"]=int(round(o.get_diagnostics().results[0].reportData.maintenance.nextMaintOdometer))
            v["onstar.airbagok"]=o.get_diagnostics().results[0].reportData.sections.airbag.status=="GREEN"
            v["onstar.localization"]=self._get_location(o.get_location().results)

            return v
        except (ConnectionResetError) as err:
            _LOGGER.debug(
                "Error getting OnStar info: %s", err)
            return None

    @property
    def status(self):
        """Return the current status."""
        return self._status

    # Formats date from 2019-10-16T10:54:52.535+02:00 to human readable
    def _get_date(self, str_date):
        date = datetime.strptime(str_date, '%Y-%m-%dT%H:%M:%S.%f%z')
        return date.strftime('%Y-%m-%d %H:%M:%S')

    # Gets latest location from table
    def _get_location(self, report):

        for r in report:
            if r.index == 0:
                self.gps_position = r.location
                return r.location

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self, **kwargs):
        """Fetch the latest status from OnStar."""
        _LOGGER.info("Update onstar data.")
        self._status = self._get_status()
