import logging

_LOGGER = logging.getLogger(__name__)
from homeassistant.util import slugify
from homeassistant.helpers.event import track_utc_time_change

from . import DOMAIN


def setup_scanner(hass, config, see, discovery_info=None):

    data = hass.data[DOMAIN]
    tracker = OnstarDeviceTracker(see, data)
    _LOGGER.info("onstar device_tracker set-up")
    tracker.setup(hass)
    return True

class OnstarDeviceTracker:
    """BMW Connected Drive device tracker."""

    def __init__(self, see, data):
        """Initialize the Tracker."""
        self._see = see
        self._data = data

    def setup(self, hass):
        """Set up a timer and start gathering devices."""
        self.update()
        track_utc_time_change(
            hass, lambda now: self.update(), second=range(0, 60, 30)
        )


    def update(self) -> None:
        """Update the device info.
        Only update the state in home assistant if tracking in
        the car is enabled.
        """
        dev_id = slugify(self._data.status['onstar.plate'])

        if self._data._pin is None:
            _LOGGER.debug("Tracking is disabled for vehicle %s", dev_id)
            return

        _LOGGER.info("Updating %s", dev_id)
        attrs = {"vin": self._data.status['onstar.vin']}
        self._see(
            dev_id=dev_id,
            host_name=self._data.status['onstar.plate'],
            gps=self._data.gps_position,
            attributes=attrs,
            icon="mdi:car",
        )