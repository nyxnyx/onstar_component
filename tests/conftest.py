"""Shared fixtures for OnStar component tests."""
import sys
from types import ModuleType
from unittest.mock import MagicMock, PropertyMock

import pytest


# ---------------------------------------------------------------------------
# Stub out heavy third-party dependencies that are not available in the test
# environment so the component modules can be imported without error.
# ---------------------------------------------------------------------------

def _create_ha_stubs():
    """Create stub modules for Home Assistant and onstar SDK."""
    stubs: dict[str, ModuleType] = {}

    def _mod(name: str) -> ModuleType:
        if name not in stubs:
            m = ModuleType(name)
            stubs[name] = m
        return stubs[name]

    # -- homeassistant core ---------------------------------------------------
    ha = _mod("homeassistant")
    ha.const = _mod("homeassistant.const")
    ha.const.CONF_USERNAME = "username"
    ha.const.CONF_PASSWORD = "password"
    ha.const.CONF_PIN = "pin"

    ha.exceptions = _mod("homeassistant.exceptions")

    class PlatformNotReady(Exception):
        pass

    ha.exceptions.PlatformNotReady = PlatformNotReady

    # helpers
    ha.helpers = _mod("homeassistant.helpers")
    ha.helpers.config_validation = _mod("homeassistant.helpers.config_validation")
    ha.helpers.config_validation.string = str
    ha.helpers.discovery = _mod("homeassistant.helpers.discovery")
    ha.helpers.discovery.load_platform = MagicMock()
    ha.helpers.entity = _mod("homeassistant.helpers.entity")
    ha.helpers.entity.Entity = type("Entity", (), {})
    ha.helpers.event = _mod("homeassistant.helpers.event")
    ha.helpers.event.track_utc_time_change = MagicMock()

    # components.sensor
    ha.components = _mod("homeassistant.components")
    ha.components.sensor = _mod("homeassistant.components.sensor")
    ha.components.sensor.SensorEntity = type(
        "SensorEntity",
        (),
        {
            "should_poll": property(lambda self: True),
            "force_update": property(lambda self: False),
        },
    )

    # util
    ha.util = _mod("homeassistant.util")

    def throttle_decorator(interval):
        def decorator(func):
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            wrapper.__wrapped__ = func
            return wrapper
        return decorator

    ha.util.Throttle = throttle_decorator
    ha.util.slugify = _mod("homeassistant.util.slugify") if "homeassistant.util.slugify" not in stubs else stubs["homeassistant.util.slugify"]
    # provide slugify as a callable
    ha_util_slugify_mod = _mod("homeassistant.util.slugify")

    def _slugify(text: str) -> str:
        return text.lower().replace(" ", "_").replace(".", "_")

    # Make the module callable via its import as `from homeassistant.util import slugify`
    ha.util.slugify = _slugify

    # voluptuous
    vol = _mod("voluptuous")
    vol.Schema = MagicMock(return_value=MagicMock())
    vol.Required = MagicMock(side_effect=lambda x: x)
    vol.Optional = MagicMock(side_effect=lambda x: x)
    vol.ALLOW_EXTRA = "ALLOW_EXTRA"

    # onstar SDK
    onstar_pkg = _mod("onstar")
    onstar_mod = _mod("onstar.onstar")
    onstar_mod.OnStar = MagicMock()

    # Register everything in sys.modules
    for name, mod in stubs.items():
        sys.modules[name] = mod


# Install stubs before any component imports happen
_create_ha_stubs()


# ---------------------------------------------------------------------------
# Reusable fixtures
# ---------------------------------------------------------------------------

SAMPLE_STATUS = {
    "onstar.plate": "ABC1234",
    "onstar.vin": "1HGCM82639A123456",
    "onstar.laststatus": "2025-01-15 10:30:00",
    "onstar.warningcount": 0,
    "onstar.errorcount": 0,
    "onstar.oillife": 85.5,
    "onstar.fuellevel": 72,
    "onstar.range": 450,
    "onstar.ignition": "OFF",
    "onstar.odometer": 45000,
    "onstar.tirelf": 230,
    "onstar.tirelr": 228,
    "onstar.tirerf": 231,
    "onstar.tirerr": 229,
    "onstar.tirestatuslf": True,
    "onstar.tirestatuslr": True,
    "onstar.tirestatusrf": True,
    "onstar.tirestatusrr": True,
    "onstar.tiresetting": "Normal",
    "onstar.ftirepressure": 230,
    "onstar.rtirepressure": 230,
    "onstar.nextmainodo": 50000,
    "onstar.nextmaindate": "2026-06-01",
    "onstar.airbagok": True,
    "onstar.localization": (48.8566, 2.3522),
}

SENSOR_TYPES = {
    "onstar.plate": ["Plate", "", "mdi:account-card-details"],
    "onstar.laststatus": ["Last updated", "", "mdi:update"],
    "onstar.warningcount": ["Warnings", "", "mdi:account-alert"],
    "onstar.errorcount": ["Errors", "", "mdi:alert-circle"],
    "onstar.oillife": ["Oil life", "%", "mdi:oil"],
    "onstar.fuellevel": ["Fuel level", "%", "mdi:gas-station"],
    "onstar.range": ["Fuel range", "km", "mdi:gas-station"],
    "onstar.ignition": ["Ignition", "", "mdi:power-standby"],
    "onstar.odometer": ["Odometer", "km", "mdi:gauge"],
    "onstar.tirelf": ["Left Front Tire", "kPa", "mdi:car"],
    "onstar.tirelr": ["Left Rear Tire", "kPa", "mdi:car-back"],
    "onstar.tirerf": ["Right Front Tire", "kPa", "mdi:car"],
    "onstar.tirerr": ["Right Rear Tire", "kPa", "mdi:car-back"],
    "onstar.tirestatuslf": ["Left Front Tire Status", None, None],
    "onstar.tirestatuslr": ["Left Rear Tire Status", None, None],
    "onstar.tirestatusrf": ["Right Front Tire Status", None, None],
    "onstar.tirestatusrr": ["Right Rear Tire Status", None, None],
    "onstar.tiresetting": ["Tire setting", None, None],
    "onstar.ftirepressure": ["Front Tires expected pressure", "kPa", None],
    "onstar.rtirepressure": ["Rear Tire expected pressure", "kPa", None],
    "onstar.nextmainodo": ["Next maintenance", "km", None],
    "onstar.nextmaindate": ["Next maintenance Date", None, "mdi:calendar"],
    "onstar.airbagok": ["Airbag status", None, None],
    "onstar.localization": ["Latest localization", None, "mdi:compass"],
    "onstar.vin": ["VIN", None, "mdi:id-card"],
}


@pytest.fixture()
def mock_data():
    """Return a mock OnStarData object with sample status and SENSOR_TYPES."""
    data = MagicMock()
    data.SENSOR_TYPES = SENSOR_TYPES.copy()
    type(data).status = PropertyMock(return_value=SAMPLE_STATUS.copy())
    data.gps_position = (48.8566, 2.3522)
    data._pin = "1234"
    data.update = MagicMock()
    return data


@pytest.fixture()
def mock_data_no_status():
    """Return a mock OnStarData object where status is None."""
    data = MagicMock()
    data.SENSOR_TYPES = SENSOR_TYPES.copy()
    type(data).status = PropertyMock(return_value=None)
    data.gps_position = None
    data._pin = "1234"
    data.update = MagicMock()
    return data


@pytest.fixture()
def mock_hass(mock_data):
    """Return a mock Home Assistant instance with OnStar data loaded."""
    hass = MagicMock()
    hass.data = {"onstar_component": mock_data}
    hass.services = MagicMock()
    return hass


@pytest.fixture()
def mock_hass_no_status(mock_data_no_status):
    """Return a mock Home Assistant instance where OnStar data has no status."""
    hass = MagicMock()
    hass.data = {"onstar_component": mock_data_no_status}
    hass.services = MagicMock()
    return hass
