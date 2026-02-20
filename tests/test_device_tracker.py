"""Tests for device_tracker.py."""
from unittest.mock import MagicMock, PropertyMock, call, patch

import pytest

from onstar_component.device_tracker import OnstarDeviceTracker, setup_scanner
from onstar_component.const import DOMAIN


# ==========================================================================
# setup_scanner tests
# ==========================================================================


class TestSetupScanner:
    """Tests for the setup_scanner function."""

    def test_returns_true(self, mock_hass, mock_data):
        see = MagicMock()
        result = setup_scanner(mock_hass, {}, see)
        assert result is True

    def test_creates_tracker(self, mock_hass, mock_data):
        """setup_scanner should create a tracker and call setup."""
        see = MagicMock()
        with patch.object(OnstarDeviceTracker, "setup") as mock_setup:
            with patch.object(OnstarDeviceTracker, "__init__", return_value=None) as mock_init:
                setup_scanner(mock_hass, {}, see)
                mock_init.assert_called_once_with(see, mock_data)


# ==========================================================================
# OnstarDeviceTracker tests
# ==========================================================================


class TestOnstarDeviceTracker:
    """Tests for the OnstarDeviceTracker class."""

    @pytest.fixture()
    def tracker(self, mock_data):
        see = MagicMock()
        return OnstarDeviceTracker(see, mock_data), see

    def test_init_stores_see_and_data(self, mock_data):
        see = MagicMock()
        tracker = OnstarDeviceTracker(see, mock_data)
        assert tracker._see is see
        assert tracker._data is mock_data

    def test_setup_calls_update(self, tracker):
        """setup() should call update() immediately."""
        t, see = tracker
        with patch.object(t, "update") as mock_update:
            hass = MagicMock()
            t.setup(hass)
            mock_update.assert_called_once()

    def test_setup_registers_time_change_listener(self, tracker):
        """setup() should register a track_utc_time_change listener."""
        t, see = tracker
        hass = MagicMock()

        with patch("onstar_component.device_tracker.track_utc_time_change") as mock_track:
            with patch.object(t, "update"):
                t.setup(hass)
            mock_track.assert_called_once()
            # First arg should be hass
            assert mock_track.call_args[0][0] is hass

    def test_update_calls_see_with_correct_data(self, mock_data):
        """update() should call self._see with device info from data."""
        see = MagicMock()
        tracker = OnstarDeviceTracker(see, mock_data)

        tracker.update()

        see.assert_called_once()
        call_kwargs = see.call_args[1]
        assert call_kwargs["host_name"] == "ABC1234"
        assert call_kwargs["gps"] == mock_data.gps_position
        assert call_kwargs["icon"] == "mdi:car"
        assert "vin" in call_kwargs["attributes"]
        assert call_kwargs["attributes"]["vin"] == "1HGCM82639A123456"

    def test_update_skips_when_pin_is_none(self, mock_data):
        """When pin is None, tracking should be disabled."""
        mock_data._pin = None
        see = MagicMock()
        tracker = OnstarDeviceTracker(see, mock_data)

        tracker.update()

        see.assert_not_called()

    def test_update_device_id_is_slugified(self, mock_data):
        """The dev_id passed to see() should be a slugified version of the plate."""
        see = MagicMock()
        tracker = OnstarDeviceTracker(see, mock_data)

        tracker.update()

        call_kwargs = see.call_args[1]
        dev_id = call_kwargs["dev_id"]
        # Should be lowercase, no spaces
        assert dev_id == dev_id.lower()
        assert " " not in dev_id


# ==========================================================================
# const.py tests
# ==========================================================================


class TestConst:
    """Tests for const.py values."""

    def test_domain_is_string(self):
        assert isinstance(DOMAIN, str)
        assert len(DOMAIN) > 0

    def test_domain_value(self):
        assert DOMAIN == "onstar_component"

    def test_onstar_components(self):
        from onstar_component.const import ONSTAR_COMPONENTS
        assert "sensor" in ONSTAR_COMPONENTS
        assert "device_tracker" in ONSTAR_COMPONENTS

    def test_min_time_between_updates(self):
        from onstar_component.const import MIN_TIME_BETWEEN_UPDATES
        assert MIN_TIME_BETWEEN_UPDATES.total_seconds() > 0
        assert MIN_TIME_BETWEEN_UPDATES.total_seconds() == 300
