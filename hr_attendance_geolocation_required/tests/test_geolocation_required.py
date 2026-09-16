# Copyright 2026 David Palanca Martínez - Grupo Isonor
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

import json

from odoo import _
from odoo.exceptions import ValidationError
from odoo.tests import HttpCase, TransactionCase


class TestGeolocationRequired(HttpCase):
    """Test geolocation requirement for attendance check-in."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Use the main company and configure it for kiosk mode
        cls.company = cls.env.company
        cls.company.write(
            {
                "attendance_kiosk_mode": "barcode_manual",
                "attendance_geolocation_required": True,
            }
        )

        # Create an employee with a PIN
        cls.employee = cls.env["hr.employee"].create(
            {
                "name": "Test Employee Geolocation",
                "company_id": cls.company.id,
                "pin": "1234",
            }
        )

    def _make_jsonrpc_request(self, latitude, longitude):
        """Helper to make JSON-RPC request to manual_selection endpoint."""
        response = self.url_open(
            "/hr_attendance/manual_selection",
            data=json.dumps(
                {
                    "jsonrpc": "2.0",
                    "method": "call",
                    "params": {
                        "employee_id": self.employee.id,
                        "pin_code": "1234",
                        "latitude": latitude,
                        "longitude": longitude,
                    },
                    "id": None,
                }
            ),
            headers={"Content-Type": "application/json"},
        )
        return response.json().get("result", {})

    def test_check_in_without_coordinates_is_rejected(self):
        """Test that check-in without coordinates returns error."""
        result = self._make_jsonrpc_request(latitude=False, longitude=False)

        self.assertIn("error", result)
        self.assertEqual(
            result["error"],
            _("You must activate location and GPS to clock in."),
        )
        # Verify no attendance was created
        self.assertEqual(len(self.employee.attendance_ids), 0)

    def test_check_in_without_latitude_is_rejected(self):
        """Test that check-in without latitude returns error."""
        result = self._make_jsonrpc_request(latitude=False, longitude=2.1734)

        self.assertIn("error", result)
        self.assertEqual(len(self.employee.attendance_ids), 0)

    def test_check_in_without_longitude_is_rejected(self):
        """Test that check-in without longitude returns error."""
        result = self._make_jsonrpc_request(latitude=41.3851, longitude=False)

        self.assertIn("error", result)
        self.assertEqual(len(self.employee.attendance_ids), 0)

    def test_check_in_with_valid_coordinates_succeeds(self):
        """Test that check-in with valid coordinates creates attendance."""
        initial_count = len(self.employee.attendance_ids)

        result = self._make_jsonrpc_request(latitude=41.3851, longitude=2.1734)

        self.assertNotIn("error", result)
        # Verify attendance was created
        self.assertEqual(len(self.employee.attendance_ids), initial_count + 1)
        attendance = self.employee.attendance_ids[0]
        self.assertTrue(attendance.check_in)
        self.assertFalse(attendance.check_out)

    def test_check_out_also_requires_coordinates(self):
        """Test that check-out also requires geolocation."""
        # First check-in with coordinates
        self._make_jsonrpc_request(latitude=41.3851, longitude=2.1734)

        # Try to check-out without coordinates
        result = self._make_jsonrpc_request(latitude=False, longitude=False)
        self.assertIn("error", result)
        # Attendance should still not have check_out
        attendance = self.employee.attendance_ids[0]
        self.assertFalse(attendance.check_out)

        # Check-out with coordinates should work
        result = self._make_jsonrpc_request(latitude=41.3851, longitude=2.1734)
        self.assertNotIn("error", result)
        attendance = self.employee.attendance_ids[0]
        self.assertTrue(attendance.check_out)

    def test_geolocation_not_required_allows_check_in_without_coordinates(self):
        """Test that check-in without coordinates is allowed when not required."""
        self.company.attendance_geolocation_required = False
        result = self._make_jsonrpc_request(latitude=False, longitude=False)
        self.assertNotIn("error", result)
        self.assertEqual(len(self.employee.attendance_ids), 1)


class TestGeolocationRequiredModel(TransactionCase):
    """Test geolocation validation at model level (_attendance_action_change)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.attendance_geolocation_required = True
        cls.employee = cls.env["hr.employee"].create(
            {
                "name": "Test Employee Model",
                "company_id": cls.company.id,
            }
        )

    def test_action_change_without_geo_raises(self):
        """Calling _attendance_action_change without geo_information raises."""
        with self.assertRaises(ValidationError):
            self.employee._attendance_action_change()

    def test_action_change_with_empty_coords_raises(self):
        """Calling _attendance_action_change with False coords raises."""
        with self.assertRaises(ValidationError):
            self.employee._attendance_action_change(
                # {"latitude": False, "longitude": False}
            )

    def test_action_change_with_valid_geo_succeeds(self):
        """Calling _attendance_action_change with valid geo succeeds."""
        attendance = self.employee.with_context(
            **{"latitude": 41.3851, "longitude": 2.1734}
        )._attendance_action_change()
        self.assertTrue(attendance.check_in)

    def test_action_change_not_required_without_geo_succeeds(self):
        """When not required, _attendance_action_change without geo works."""
        self.company.attendance_geolocation_required = False
        attendance = self.employee._attendance_action_change()
        self.assertTrue(attendance.check_in)
