"""Constants for the OnStar component."""
from datetime import timedelta

DOMAIN = "onstar_component"
ONSTAR_COMPONENTS = ["sensor", "device_tracker"]
MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=300)
