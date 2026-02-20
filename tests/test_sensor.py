"""Tests for sensor.py."""
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from onstar_component.sensor import OnStarSensor, setup_platform
from onstar_component.const import DOMAIN


# ==========================================================================
# setup_platform tests
# ==========================================================================


class TestSetupPlatform:
    """Tests for the setup_platform function."""

    def test_raises_platform_not_ready_when_status_is_none(
        self, mock_hass_no_status, mock_data_no_status
    ):
        """When data.status is None, PlatformNotReady should be raised."""
        from homeassistant.exceptions import PlatformNotReady

        add_entities = MagicMock()
        with pytest.raises(PlatformNotReady):
            setup_platform(mock_hass_no_status, {}, add_entities)

    def test_creates_entities_for_known_sensor_types(
        self, mock_hass, mock_data
    ):
        """Each key in data.status that exists in SENSOR_TYPES gets an entity."""
        added: list = []
        add_entities = MagicMock(side_effect=lambda ents, update: added.extend(ents))

        setup_platform(mock_hass, {}, add_entities)

        # All keys in SAMPLE_STATUS are also in SENSOR_TYPES, so all should be added
        assert len(added) == len(mock_data.status)
        assert all(isinstance(e, OnStarSensor) for e in added)

    def test_skips_unknown_sensor_types(self, mock_hass, mock_data):
        """Keys in data.status NOT in SENSOR_TYPES should be skipped with a warning."""
        # Inject an unknown key into status
        status_with_unknown = mock_data.status.copy()
        status_with_unknown["onstar.unknown_sensor"] = "value"
        type(mock_data).status = PropertyMock(return_value=status_with_unknown)

        added: list = []
        add_entities = MagicMock(side_effect=lambda ents, update: added.extend(ents))

        with patch("onstar_component.sensor._LOGGER") as mock_logger:
            setup_platform(mock_hass, {}, add_entities)
            mock_logger.warning.assert_called()

        # The unknown sensor should NOT generate an entity
        assert len(added) == len(status_with_unknown) - 1

    def test_calls_data_update_with_no_throttle(self, mock_hass, mock_data):
        """setup_platform should force an initial data update."""
        add_entities = MagicMock()
        setup_platform(mock_hass, {}, add_entities)
        mock_data.update.assert_called_once_with(no_throttle=True)

    def test_add_entities_called_with_update_flag(self, mock_hass, mock_data):
        """add_entities should be called with update_before_add=True."""
        add_entities = MagicMock()
        setup_platform(mock_hass, {}, add_entities)
        add_entities.assert_called_once()
        _, kwargs_or_args = add_entities.call_args
        # Second positional arg should be True
        assert add_entities.call_args[0][1] is True

    def test_empty_status_creates_no_entities(self, mock_hass, mock_data):
        """An empty status dict should result in zero entities."""
        type(mock_data).status = PropertyMock(return_value={})

        added: list = []
        add_entities = MagicMock(side_effect=lambda ents, update: added.extend(ents))

        setup_platform(mock_hass, {}, add_entities)
        assert len(added) == 0


# ==========================================================================
# OnStarSensor tests
# ==========================================================================


class TestOnStarSensor:
    """Tests for the OnStarSensor entity."""

    @pytest.fixture()
    def sensor(self, mock_data):
        """Create a sensor for 'onstar.fuellevel'."""
        return OnStarSensor(mock_data, "onstar.fuellevel")

    # -- Initialization -------------------------------------------------------

    def test_name(self, sensor):
        """Sensor name should come from SENSOR_TYPES."""
        assert sensor._attr_name == "Fuel level"

    def test_unique_id(self, sensor):
        """unique_id should be derived from sensor_type with dots replaced."""
        assert sensor._attr_unique_id == "onstar_onstar_fuellevel"

    def test_unit_of_measurement(self, sensor):
        """Unit should come from SENSOR_TYPES."""
        assert sensor._attr_native_unit_of_measurement == "%"

    def test_icon(self, sensor):
        """Icon should come from SENSOR_TYPES."""
        assert sensor._attr_icon == "mdi:gas-station"

    def test_initial_state_is_none(self, sensor):
        """State should be None before the first update."""
        assert sensor.native_value is None

    # -- Properties -----------------------------------------------------------

    def test_should_poll(self, sensor):
        assert sensor.should_poll is True

    def test_force_update(self, sensor):
        assert sensor.force_update is False

    # -- display_state --------------------------------------------------------

    def test_display_state_on(self, sensor):
        """When status exists, display_state returns 'ON'."""
        assert sensor.display_state() == "ON"

    def test_display_state_off(self, mock_data_no_status):
        """When status is None, display_state returns 'OFF'."""
        sensor = OnStarSensor(mock_data_no_status, "onstar.fuellevel")
        assert sensor.display_state() == "OFF"

    # -- extra_state_attributes -----------------------------------------------

    def test_extra_state_attributes_returns_dict(self, sensor):
        attrs = sensor.extra_state_attributes
        assert isinstance(attrs, dict)
        assert "state" in attrs

    def test_extra_state_attributes_contains_display_state(self, sensor):
        attrs = sensor.extra_state_attributes
        assert attrs["state"] == sensor.display_state()

    # -- update ---------------------------------------------------------------

    def test_update_populates_state(self, sensor):
        """After update, native_value should reflect data.status."""
        sensor.update()
        assert sensor.native_value == 72  # fuel level from SAMPLE_STATUS

    def test_update_sets_none_when_status_is_none(self, mock_data_no_status):
        """When data.status is None, state should be cleared."""
        sensor = OnStarSensor(mock_data_no_status, "onstar.fuellevel")
        sensor._state = "stale"
        sensor.update()
        assert sensor.native_value is None

    def test_update_sets_none_for_missing_type(self, mock_data):
        """When the sensor type is no longer in status, state should be None."""
        # Remove the key from status
        status = mock_data.status.copy()
        del status["onstar.fuellevel"]
        type(mock_data).status = PropertyMock(return_value=status)

        sensor = OnStarSensor(mock_data, "onstar.fuellevel")
        sensor.update()
        assert sensor.native_value is None

    # -- Various sensor types -------------------------------------------------

    def test_sensor_with_no_unit(self, mock_data):
        """Sensors like 'onstar.tirestatuslf' have None unit and icon."""
        sensor = OnStarSensor(mock_data, "onstar.tirestatuslf")
        assert sensor._attr_native_unit_of_measurement is None
        assert sensor._attr_icon is None
        assert sensor._attr_name == "Left Front Tire Status"

    def test_sensor_with_km_unit(self, mock_data):
        """Sensors like 'onstar.odometer' use km."""
        sensor = OnStarSensor(mock_data, "onstar.odometer")
        assert sensor._attr_native_unit_of_measurement == "km"
        sensor.update()
        assert sensor.native_value == 45000

    def test_unique_id_is_unique_per_type(self, mock_data):
        """Each sensor type should produce a distinct unique_id."""
        s1 = OnStarSensor(mock_data, "onstar.plate")
        s2 = OnStarSensor(mock_data, "onstar.vin")
        assert s1._attr_unique_id != s2._attr_unique_id

    def test_all_sample_sensors_can_be_created(self, mock_data):
        """Verify every key in SENSOR_TYPES can produce a valid sensor."""
        for sensor_type in mock_data.SENSOR_TYPES:
            sensor = OnStarSensor(mock_data, sensor_type)
            assert sensor._attr_name is not None
            assert sensor._attr_unique_id.startswith("onstar_")
