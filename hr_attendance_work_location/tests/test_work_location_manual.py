# Copyright 2026 Binhex
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import json

from odoo.tests.common import HttpCase, TransactionCase


class TestWorkLocationManualModel(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.work_location_mode = "automatic"
        cls.company.work_location_required = False
        cls.company.manual_work_location_id = False

        cls.addr_office = cls.env["res.partner"].create({"name": "Office Address"})
        cls.addr_home = cls.env["res.partner"].create({"name": "Home Address"})
        cls.addr_excluded = cls.env["res.partner"].create({"name": "Excluded Address"})
        cls.loc_office = cls.env["hr.work.location"].create(
            {
                "name": "Office",
                "company_id": cls.company.id,
                "address_id": cls.addr_office.id,
                "location_type": "office",
            }
        )
        cls.loc_home = cls.env["hr.work.location"].create(
            {
                "name": "Home",
                "company_id": cls.company.id,
                "address_id": cls.addr_home.id,
                "location_type": "other",
            }
        )
        cls.loc_excluded = cls.env["hr.work.location"].create(
            {
                "name": "Excluded",
                "company_id": cls.company.id,
                "address_id": cls.addr_excluded.id,
                "location_type": "other",
                "exclude_from_attendance": True,
            }
        )
        cls.employee = cls.env["hr.employee"].create(
            {"name": "Test Employee", "company_id": cls.company.id}
        )

    def test_work_location_mode_default(self):
        self.assertEqual(self.company.work_location_mode, "automatic")

    def test_work_location_mode_selection(self):
        self.company.work_location_mode = "manual"
        self.assertEqual(self.company.work_location_mode, "manual")

    def test_default_work_location_propagates(self):
        self.company.manual_work_location_id = self.loc_office
        self.assertEqual(self.company.manual_work_location_id, self.loc_office)

    def test_work_location_required_flag(self):
        self.company.work_location_required = True
        self.assertTrue(self.company.work_location_required)

    def test_settings_bridge_propagates_to_company(self):
        self.company.work_location_mode = "automatic"
        settings = self.env["res.config.settings"].create(
            {"work_location_mode": "manual"}
        )
        settings.execute()
        self.assertEqual(self.company.work_location_mode, "manual")


class TestWorkLocationManualController(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.attendance_kiosk_key = "test-token-manual"
        cls.company.work_location_mode = "manual"
        cls.company.work_location_required = False
        cls.company.manual_work_location_id = False

        cls.addr_office = cls.env["res.partner"].create({"name": "Office Address"})
        cls.addr_excluded = cls.env["res.partner"].create({"name": "Excluded Address"})
        cls.loc_office = cls.env["hr.work.location"].create(
            {
                "name": "Office",
                "company_id": cls.company.id,
                "address_id": cls.addr_office.id,
                "location_type": "office",
            }
        )
        cls.loc_excluded = cls.env["hr.work.location"].create(
            {
                "name": "Excluded",
                "company_id": cls.company.id,
                "address_id": cls.addr_excluded.id,
                "location_type": "other",
                "exclude_from_attendance": True,
            }
        )
        cls.employee = cls.env["hr.employee"].create(
            {
                "name": "Test Employee",
                "company_id": cls.company.id,
                "barcode": "TESTBC01",
            }
        )

    def test_preflight_returns_employee_state(self):
        """Preflight endpoint returns correct attendance_state."""
        result = self.url_open(
            "/hr_attendance_work_location/attendance_preflight",
            data=json.dumps(
                {
                    "jsonrpc": "2.0",
                    "method": "call",
                    "params": {
                        "token": "test-token-manual",
                        "barcode": "TESTBC01",
                    },
                }
            ),
            headers={"Content-Type": "application/json"},
        )
        data = result.json()
        self.assertEqual(data["result"]["attendance_state"], "checked_out")

    def test_preflight_returns_work_locations(self):
        """Preflight endpoint returns available locations."""
        result = self.url_open(
            "/hr_attendance_work_location/attendance_preflight",
            data=json.dumps(
                {
                    "jsonrpc": "2.0",
                    "method": "call",
                    "params": {
                        "token": "test-token-manual",
                        "barcode": "TESTBC01",
                    },
                }
            ),
            headers={"Content-Type": "application/json"},
        )
        data = result.json()
        location_ids = [loc["id"] for loc in data["result"]["work_locations"]]
        self.assertIn(self.loc_office.id, location_ids)
        self.assertNotIn(self.loc_excluded.id, location_ids)

    def test_kiosk_location_settings(self):
        """New endpoint returns correct data."""
        result = self.url_open(
            "/hr_attendance_work_location/kiosk_location_settings",
            data=json.dumps(
                {
                    "jsonrpc": "2.0",
                    "method": "call",
                    "params": {"token": "test-token-manual"},
                }
            ),
            headers={"Content-Type": "application/json"},
        )
        data = result.json()
        self.assertEqual(data["result"]["work_location_mode"], "manual")
        self.assertFalse(data["result"]["work_location_required"])
