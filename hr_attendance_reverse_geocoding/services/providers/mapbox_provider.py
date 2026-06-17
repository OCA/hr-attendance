# Copyright 2026 Binhex Systems Solutions S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import requests

from .base_provider import BaseGeocodingProvider

MAPBOX_REQUEST_TIMEOUT = 10  # seconds


class MapboxGeocodingProvider(BaseGeocodingProvider):
    """
    Reverse geocoding provider using Mapbox API.

    Documentation: https://docs.mapbox.com/api/search/geocoding/
    """

    PROVIDER_NAME = "mapbox"

    def reverse_geocode(self, latitude, longitude):
        """
        Call Mapbox Geocoding API to get address from GPS coordinates.

        :param latitude: float - latitude
        :param longitude: float - longitude
        :return: dict with address, map_url and provider
        :raises: requests.RequestException if network error
        :raises: ValueError if response is invalid or empty
        """

        params = {
            "access_token": self.api_key,
            "language": "es",
            "limit": 1,
            "types": "address,place,locality,neighborhood",
        }

        try:
            response = requests.get(
                self.endpoint + f"?longitude={longitude}&latitude={latitude}",
                params=params,
                timeout=MAPBOX_REQUEST_TIMEOUT,
            )
            response.raise_for_status()
        except requests.Timeout as e:
            raise Exception(
                f"Mapbox API timeout after {MAPBOX_REQUEST_TIMEOUT}s "
                f"for coords ({latitude}, {longitude})"
            ) from e
        except requests.HTTPError as e:
            raise Exception(f"Mapbox API HTTP error {response.status_code}: {e}") from e
        except requests.RequestException as e:
            raise Exception(f"Mapbox API network error: {e}") from e

        data = response.json()
        features = data.get("features", [])

        if not features:
            raise ValueError(f"Mapbox found no address for ({latitude}, {longitude})")
        address = features[0]["properties"].get("full_address", "")

        return {
            "address": address,
            "map_url": self.build_map_url(latitude, longitude),
            "provider": self.PROVIDER_NAME,
        }

    def build_map_url(self, latitude, longitude):
        """Generate Google Maps link for visualization."""
        return f"https://www.google.com/maps?q={latitude},{longitude}"
