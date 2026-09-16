# Copyright 2026 Binhex Systems Solutions S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from datetime import datetime
from unittest.mock import patch

from odoo import tools
from odoo.tests.common import TransactionCase


class TestHrAttendanceReverseGeocoding(TransactionCase):
    def setUp(self):
        super().setUp()
        self.hr_attendance = self.env["hr.attendance"]
        self.hr_employee = self.env["hr.employee"]
        self.employee = self.hr_employee.create({"name": "Employee A"})
        self.attendance = self.hr_attendance.create(
            {
                "employee_id": self.employee.id,
                "check_in": datetime(2026, 2, 1, 9, 0, 0, 0),
            }
        )
        self.latitude = 40.74817224747897
        self.longitude = -73.98586825065489
        self.PROVIDER_NAME = "mapbox"
        self.address = "17 West 33rd Street, New York, New York 10118, United States"
        self.map_url = (
            "https://www.google.com/maps?q=40.74817224747897,-73.98586825065489"
        )
        self.geocode_cache = self.env["hr.attendance.geocode.cache"]
        self.dp = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("hr_attendance_reverse_geocoding.api_key", 4)
        )

    @patch(
        "odoo.addons.hr_attendance_reverse_geocoding.services."
        "geocoding_service.GeocodingService.get_address"
    )
    def test_reverse_geocoding_for_check_in(self, mock_get_address):
        mock_get_address.return_value = {
            "address": self.address,
            "map_url": self.map_url,
            "provider": self.PROVIDER_NAME,
        }

        prefix = "check_in"

        vals = {
            "check_in_latitude": self.latitude,
            "check_in_longitude": self.longitude,
        }
        self.attendance.write(vals)

        self.attendance._resolve_geocoding(prefix, vals)

        self.assertEqual(self.attendance.check_in_address, self.address)
        self.assertEqual(self.attendance.check_in_geocode_status, "done")
        self.assertEqual(self.attendance.check_in_geocode_provider, self.PROVIDER_NAME)
        self.assertEqual(self.attendance.check_in_map_url, self.map_url)

    @patch(
        "odoo.addons.hr_attendance_reverse_geocoding.services."
        "geocoding_service.GeocodingService.get_address"
    )
    def test_reverse_geocoding_for_check_out(self, mock_get_address):
        mock_get_address.return_value = {
            "address": self.address,
            "map_url": self.map_url,
            "provider": self.PROVIDER_NAME,
        }

        prefix = "check_out"

        vals = {
            "check_out_latitude": self.latitude,
            "check_out_longitude": self.longitude,
            "check_out": datetime(2026, 2, 1, 16, 0, 0, 0),
        }
        self.attendance.write(vals)

        self.attendance._resolve_geocoding(prefix, vals)

        self.assertEqual(self.attendance.check_out_address, self.address)
        self.assertEqual(self.attendance.check_out_geocode_status, "done")
        self.assertEqual(self.attendance.check_out_geocode_provider, self.PROVIDER_NAME)
        self.assertEqual(self.attendance.check_out_map_url, self.map_url)

    def test_reverse_geocoding_for_check_in_with_cache(self):
        latitude_normalize = tools.float_round(self.latitude, precision_digits=self.dp)
        longtide_normalize = tools.float_round(self.longitude, precision_digits=self.dp)
        values = {
            "latitude_normalize": latitude_normalize,
            "longtide_normalize": longtide_normalize,
            "address": self.address,
            "provider": self.PROVIDER_NAME,
            "map_url": self.map_url,
        }
        self.geocode_cache.create(values)
        prefix = "check_in"
        vals = {
            "check_in_latitude": self.latitude,
            "check_in_longitude": self.longitude,
        }
        self.attendance.write(vals)

        self.attendance._resolve_geocoding(prefix, vals)

        self.assertEqual(self.attendance.check_in_address, self.address)
        self.assertEqual(self.attendance.check_in_geocode_status, "done")
        self.assertEqual(self.attendance.check_in_geocode_provider, self.PROVIDER_NAME)
        self.assertEqual(self.attendance.check_in_map_url, self.map_url)

    def test_reverse_geocoding_for_check_out_with_cache(self):
        latitude_normalize = tools.float_round(self.latitude, precision_digits=self.dp)
        longtide_normalize = tools.float_round(self.longitude, precision_digits=self.dp)
        values = {
            "latitude_normalize": latitude_normalize,
            "longtide_normalize": longtide_normalize,
            "address": self.address,
            "provider": self.PROVIDER_NAME,
            "map_url": self.map_url,
        }
        self.geocode_cache.create(values)
        prefix = "check_out"
        vals = {
            "check_out_latitude": self.latitude,
            "check_out_longitude": self.longitude,
            "check_out": datetime(2026, 2, 1, 16, 0, 0, 0),
        }
        self.attendance.write(vals)

        self.attendance._resolve_geocoding(prefix, vals)

        self.assertEqual(self.attendance.check_out_address, self.address)
        self.assertEqual(self.attendance.check_out_geocode_status, "done")
        self.assertEqual(self.attendance.check_out_geocode_provider, self.PROVIDER_NAME)
        self.assertEqual(self.attendance.check_out_map_url, self.map_url)
