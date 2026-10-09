# Copyright 2026 Binhex Systems Solutions S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging
from abc import ABC, abstractmethod

_logger = logging.getLogger(__name__)


class BaseGeocodingProvider(ABC):
    """
    Abstract base class for reverse geocoding providers.

    Implements the Strategy pattern to decouple business logic
    from concrete external providers.

    To add a new provider, just inherit from this class
    and implement `reverse_geocode`.
    """

    PROVIDER_NAME = None  # Unique provider identifier, e.g.: 'mapbox'

    def __init__(self, api_key=None, endpoint=None):
        self.api_key = api_key
        self.endpoint = endpoint

    @abstractmethod
    def reverse_geocode(self, latitude, longitude):
        """
        Translate GPS coordinates to readable address.

        :param latitude: float - latitude
        :param longitude: float - longitude
        :return: dict with keys:
            - address (str): readable address
            - map_url (str|None): external link to map
            - provider (str): identifier of provider used
        :raises: Exception if external service fails
        """

    def build_map_url(self, latitude, longitude):
        """
        Generate external map link from coordinates.
        Can be overridden by each provider.
        By default generates a link to OpenStreetMap.
        """
        return (
            f"https://www.openstreetmap.org/?mlat={latitude}&mlon={longitude}&zoom=17"
        )
