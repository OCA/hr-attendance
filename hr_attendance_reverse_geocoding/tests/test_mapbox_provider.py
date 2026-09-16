# Copyright 2026 Binhex Systems Solutions S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from unittest.mock import MagicMock, patch

import requests

from odoo.tests.common import TransactionCase

from odoo.addons.hr_attendance_reverse_geocoding.services.providers.mapbox_provider import (
    MapboxGeocodingProvider,
)


class TestMapboxGeocodingProvider(TransactionCase):
    def setUp(self):
        super().setUp()
        self.provider = MapboxGeocodingProvider(
            api_key="fake-api-key",
            endpoint="https://api.mapbox.com/search/geocode/v6/reverse",
        )
        self.latitude = 40.74817224747897
        self.longitude = -73.98586825065489

    @patch(
        "odoo.addons.hr_attendance_reverse_geocoding.services."
        "providers.mapbox_provider.requests.get"
    )
    def test_reverse_geocode_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "features": [
                {
                    "properties": {
                        "full_address": "17 West 33rd Street, New York, "
                        "New York 10118, United States"
                    }
                }
            ]
        }
        mock_get.return_value = mock_response

        result = self.provider.reverse_geocode(self.latitude, self.longitude)

        self.assertEqual(
            result["address"],
            "17 West 33rd Street, New York, New York 10118, United States",
        )
        self.assertEqual(result["provider"], "mapbox")
        self.assertEqual(
            result["map_url"],
            f"https://www.google.com/maps?q={self.latitude},{self.longitude}",
        )

    @patch(
        "odoo.addons.hr_attendance_reverse_geocoding.services."
        "providers.mapbox_provider.requests.get"
    )
    def test_reverse_geocode_no_features_raises_value_error(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"features": []}
        mock_get.return_value = mock_response

        with self.assertRaises(ValueError):
            self.provider.reverse_geocode(self.latitude, self.longitude)

    @patch(
        "odoo.addons.hr_attendance_reverse_geocoding.services."
        "providers.mapbox_provider.requests.get"
    )
    def test_reverse_geocode_timeout_raises_exception(self, mock_get):
        mock_get.side_effect = requests.Timeout("timed out")

        with self.assertRaises(Exception) as cm:
            self.provider.reverse_geocode(self.latitude, self.longitude)
        self.assertIn("Mapbox API timeout", str(cm.exception))

    @patch(
        "odoo.addons.hr_attendance_reverse_geocoding.services."
        "providers.mapbox_provider.requests.get"
    )
    def test_reverse_geocode_http_error_raises_exception(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = requests.HTTPError(
            "Unauthorized", response=mock_response
        )
        mock_get.return_value = mock_response

        with self.assertRaises(Exception) as cm:
            self.provider.reverse_geocode(self.latitude, self.longitude)
        self.assertIn("Mapbox API HTTP error", str(cm.exception))

    @patch(
        "odoo.addons.hr_attendance_reverse_geocoding.services."
        "providers.mapbox_provider.requests.get"
    )
    def test_reverse_geocode_network_error_raises_exception(self, mock_get):
        mock_get.side_effect = requests.ConnectionError("network down")

        with self.assertRaises(Exception) as cm:
            self.provider.reverse_geocode(self.latitude, self.longitude)
        self.assertIn("Mapbox API network error", str(cm.exception))
