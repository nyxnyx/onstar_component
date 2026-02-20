"""Tests for __init__.py (setup + OnStarData)."""
from datetime import datetime
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from onstar_component import setup, OnStarData
from onstar_component.const import DOMAIN, ONSTAR_COMPONENTS


# ==========================================================================
# setup() tests
# ==========================================================================


class TestSetup:
    """Tests for the component's setup function."""

    @pytest.fixture()
    def valid_config(self):
        return {
            DOMAIN: {
                "username": "user@example.com",
                "password": "s3cret",
                "pin": "1234",
            }
        }

    def test_setup_returns_true_with_valid_config(self, valid_config):
        hass = MagicMock()
        hass.data = {}
        hass.services = MagicMock()

        with patch("onstar_component.discovery") as mock_discovery:
            result = setup(hass, valid_config)

        assert result is True

    def test_setup_stores_data_in_hass(self, valid_config):
        hass = MagicMock()
        hass.data = {}
        hass.services = MagicMock()

        with patch("onstar_component.discovery"):
            setup(hass, valid_config)

        assert DOMAIN in hass.data
        assert isinstance(hass.data[DOMAIN], OnStarData)

    def test_setup_registers_update_service(self, valid_config):
        hass = MagicMock()
        hass.data = {}
        hass.services = MagicMock()

        with patch("onstar_component.discovery"):
            setup(hass, valid_config)

        hass.services.register.assert_called_once()
        call_args = hass.services.register.call_args
        assert call_args[0][0] == DOMAIN
        assert call_args[0][1] == "update_state"

    def test_setup_loads_all_platforms(self, valid_config):
        hass = MagicMock()
        hass.data = {}
        hass.services = MagicMock()

        with patch("onstar_component.discovery") as mock_discovery:
            setup(hass, valid_config)

        assert mock_discovery.load_platform.call_count == len(ONSTAR_COMPONENTS)
        loaded = [
            call[0][1] for call in mock_discovery.load_platform.call_args_list
        ]
        for comp in ONSTAR_COMPONENTS:
            assert comp in loaded

    def test_setup_returns_false_when_base_config_is_none(self):
        hass = MagicMock()
        result = setup(hass, None)
        assert result is False

    def test_setup_returns_false_when_domain_config_missing(self):
        hass = MagicMock()
        result = setup(hass, {"other_domain": {}})
        assert result is False

    def test_setup_handles_missing_pin(self):
        """PIN is optional; setup should still succeed without it."""
        config = {
            DOMAIN: {
                "username": "user@example.com",
                "password": "s3cret",
            }
        }
        hass = MagicMock()
        hass.data = {}
        hass.services = MagicMock()

        with patch("onstar_component.discovery"):
            result = setup(hass, config)

        assert result is True
        assert hass.data[DOMAIN]._pin is None

    def test_update_service_calls_data_update(self, valid_config):
        """The registered service callback should call data.update()."""
        hass = MagicMock()
        hass.data = {}
        hass.services = MagicMock()

        with patch("onstar_component.discovery"):
            setup(hass, valid_config)

        # Extract the registered callback
        register_call = hass.services.register.call_args
        update_callback = register_call[0][2]

        # Mock the data's update method
        hass.data[DOMAIN].update = MagicMock()
        update_callback(MagicMock())  # simulate service call

        hass.data[DOMAIN].update.assert_called_once()


# ==========================================================================
# OnStarData tests
# ==========================================================================


class TestOnStarData:
    """Tests for the OnStarData data class."""

    def test_init_stores_credentials(self):
        data = OnStarData("user", "pass", "1234")
        assert data._username == "user"
        assert data._password == "pass"
        assert data._pin == "1234"

    def test_init_status_is_none(self):
        data = OnStarData("user", "pass", "1234")
        assert data.status is None

    def test_init_gps_position_is_none(self):
        data = OnStarData("user", "pass", "1234")
        assert data.gps_position is None

    def test_sensor_types_populated(self):
        data = OnStarData("user", "pass", "1234")
        assert len(data.SENSOR_TYPES) > 0
        assert "onstar.plate" in data.SENSOR_TYPES
        assert "onstar.vin" in data.SENSOR_TYPES

    def test_sensor_types_have_three_elements(self):
        """Each SENSOR_TYPE entry should be [name, unit, icon]."""
        data = OnStarData("user", "pass", "1234")
        for key, value in data.SENSOR_TYPES.items():
            assert len(value) == 3, f"{key} should have 3 elements"
            assert isinstance(value[0], str), f"{key} name should be a string"

    def test_status_property_does_not_trigger_update(self):
        """The status property should NOT call self.update() anymore."""
        data = OnStarData("user", "pass", "1234")
        data.update = MagicMock()
        _ = data.status
        data.update.assert_not_called()

    def test_update_calls_get_status(self):
        """update() should delegate to _get_status()."""
        data = OnStarData("user", "pass", "1234")
        data._get_status = MagicMock(return_value={"onstar.plate": "XYZ"})
        data.update()
        data._get_status.assert_called_once()
        assert data.status == {"onstar.plate": "XYZ"}

    def test_update_sets_none_on_connection_error(self):
        """If _get_status returns None (connection error), status should be None."""
        data = OnStarData("user", "pass", "1234")
        data._get_status = MagicMock(return_value=None)
        data.update()
        assert data.status is None

    def test_get_date_formatting(self):
        """_get_date should parse ISO-8601 and return 'YYYY-MM-DD HH:MM:SS'."""
        data = OnStarData("user", "pass", "1234")
        result = data._get_date("2019-10-16T10:54:52.535+02:00")
        assert result == "2019-10-16 10:54:52"

    def test_get_date_different_timezone(self):
        data = OnStarData("user", "pass", "1234")
        result = data._get_date("2025-06-01T08:00:00.000+00:00")
        assert result == "2025-06-01 08:00:00"

    def test_get_location_returns_first_index_zero(self):
        """_get_location should return the location of the entry with index 0."""
        data = OnStarData("user", "pass", "1234")

        entry_0 = MagicMock()
        entry_0.index = 0
        entry_0.location = (51.5074, -0.1278)

        entry_1 = MagicMock()
        entry_1.index = 1
        entry_1.location = (48.8566, 2.3522)

        result = data._get_location([entry_1, entry_0])
        assert result == (51.5074, -0.1278)
        assert data.gps_position == (51.5074, -0.1278)

    def test_get_location_returns_none_when_no_index_zero(self):
        """If no entry has index 0, _get_location returns None."""
        data = OnStarData("user", "pass", "1234")

        entry = MagicMock()
        entry.index = 5

        result = data._get_location([entry])
        assert result is None

    def test_get_location_empty_report(self):
        data = OnStarData("user", "pass", "1234")
        result = data._get_location([])
        assert result is None

    def test_get_status_returns_none_on_connection_error(self):
        """_get_status should catch ConnectionResetError and return None."""
        data = OnStarData("user", "pass", "1234")

        with patch("onstar_component.asyncio") as mock_asyncio:
            mock_loop = MagicMock()
            mock_asyncio.new_event_loop.return_value = mock_loop
            mock_loop.run_until_complete.side_effect = ConnectionResetError("reset")

            result = data._get_status()

        assert result is None

    def test_pin_is_optional(self):
        """Data object should work fine with pin=None."""
        data = OnStarData("user", "pass", None)
        assert data._pin is None
