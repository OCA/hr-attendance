# Copyright 2026 Binhex
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields

from odoo.addons.base.tests.common import BaseCommon

# Barcelona, Plaça Catalunya — reference GPS point for all tests
_LAT = 41.38694
_LON = 2.16992


class TestHrAttendanceWorkLocation(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.employee = cls.env["hr.employee"].create({"name": "Test Employee"})
        cls.tol = cls.env.company.geo_tolerance_meters
        # Coords live on res.partner (address_id), not on hr.work.location
        cls.address_office = cls.env["res.partner"].create(
            {
                "name": "Office Address",
                "partner_latitude": _LAT,
                "partner_longitude": _LON,
            }
        )
        cls.loc_office = cls.env["hr.work.location"].create(
            {
                "name": "Office",
                "company_id": cls.env.company.id,
                "address_id": cls.address_office.id,
                "location_type": "office",
            }
        )
        # ~1.1 km away — clearly outside tolerance of the office
        cls.address_warehouse = cls.env["res.partner"].create(
            {
                "name": "Warehouse Address",
                "partner_latitude": _LAT + 0.01,
                "partner_longitude": _LON + 0.01,
            }
        )
        cls.loc_warehouse = cls.env["hr.work.location"].create(
            {
                "name": "Warehouse",
                "company_id": cls.env.company.id,
                "address_id": cls.address_warehouse.id,
                "location_type": "other",
            }
        )

    # ------------------------------------------------------------------ helpers

    def _make_attendance(
        self, in_lat=None, in_lon=None, out_lat=None, out_lon=None, **extra
    ):
        vals = {
            "employee_id": self.employee.id,
            "check_in": fields.Datetime.to_string(
                fields.Datetime.from_string("2026-03-26 08:00:00")
            ),
        }
        if in_lat is not None:
            vals["in_latitude"] = in_lat
        if in_lon is not None:
            vals["in_longitude"] = in_lon
        if out_lat is not None and out_lon is not None:
            vals["check_out"] = fields.Datetime.to_string(
                fields.Datetime.from_string("2026-03-26 17:00:00")
            )
            vals["out_latitude"] = out_lat
            vals["out_longitude"] = out_lon
        vals.update(extra)
        return self.env["hr.attendance"].create(vals)

    # ------------------------------------------------------------------ tests

    def test_check_in_coords_assign_work_location(self):
        """Exact check-in coords → in_work_location_id resolved."""
        att = self._make_attendance(in_lat=_LAT, in_lon=_LON)
        self.assertEqual(att.in_work_location_id, self.loc_office)

    def test_check_out_coords_assign_work_location(self):
        """Exact check-out coords → out_work_location_id resolved."""
        att = self._make_attendance(
            in_lat=_LAT, in_lon=_LON, out_lat=_LAT, out_lon=_LON
        )
        self.assertEqual(att.out_work_location_id, self.loc_office)

    def test_no_coords_leaves_locations_false(self):
        """No GPS coords → both location fields are False."""
        att = self._make_attendance()
        self.assertFalse(att.in_work_location_id)
        self.assertFalse(att.out_work_location_id)

    def test_coords_outside_tolerance_no_match(self):
        """Coords further than 2× tolerance from every location → False."""
        far_lat = _LAT + 3 * self.tol / 111_320.0
        far_lon = _LON + 3 * self.tol / 111_320.0
        att = self._make_attendance(in_lat=far_lat, in_lon=far_lon)
        self.assertFalse(att.in_work_location_id)

    def test_closest_location_selected_when_multiple_candidates(self):
        """When two locations fall within tolerance, the nearest one wins."""
        address_near = self.env["res.partner"].create(
            {
                "name": "Near Office Address",
                "partner_latitude": _LAT + self.tol * 0.8 / 111_320.0,
                "partner_longitude": _LON + self.tol * 0.8 / 111_320.0,
            }
        )
        loc_near = self.env["hr.work.location"].create(
            {
                "name": "Near Office",
                "company_id": self.env.company.id,
                "address_id": address_near.id,
                "location_type": "office",
            }
        )
        try:
            # loc_office is at (_LAT, _LON) — 0 distance from the check-in
            # loc_near is 0.8×TOL away — further, so loc_office must win
            att = self._make_attendance(in_lat=_LAT, in_lon=_LON)
            self.assertEqual(att.in_work_location_id, self.loc_office)
        finally:
            loc_near.unlink()
            address_near.unlink()

    def test_excluded_location_is_not_matched(self):
        """A location with exclude_from_attendance=True is never assigned."""
        self.loc_office.write({"exclude_from_attendance": True})
        try:
            att = self._make_attendance(in_lat=_LAT, in_lon=_LON)
            self.assertFalse(att.in_work_location_id)
        finally:
            self.loc_office.write({"exclude_from_attendance": False})

    def test_manual_override_preserved_on_coord_change(self):
        """Manually set in_work_location_id is not overwritten on coord update."""
        att = self._make_attendance()
        # Manually assign warehouse (compute ran as False — no coords yet)
        att.in_work_location_id = self.loc_warehouse
        # Write coords that would normally resolve to loc_office
        att.write({"in_latitude": _LAT, "in_longitude": _LON})
        # The compute must skip because in_work_location_id is already truthy
        self.assertEqual(
            att.in_work_location_id,
            self.loc_warehouse,
            "Manual override must be preserved when dependencies change",
        )

    def test_default_tolerance_is_111_meters(self):
        """Default geo_tolerance_meters is 111.0."""
        self.assertEqual(self.env.company.geo_tolerance_meters, 111.0)

    def test_sql_constraint_rejects_negative_tolerance(self):
        """SQL constraint prevents negative geo_tolerance_meters."""
        from psycopg2 import IntegrityError

        with self.assertRaises(IntegrityError):
            self.env.company.geo_tolerance_meters = -1.0
            self.env.company.flush_recordset()

    def test_settings_bridge_propagates_to_company(self):
        """Setting geo_tolerance_meters via ResConfigSettings → company."""
        self.env.company.geo_tolerance_meters = 0.0
        settings = self.env["res.config.settings"].create(
            {"geo_tolerance_meters": 50.0}
        )
        settings.execute()
        self.assertEqual(self.env.company.geo_tolerance_meters, 50.0)

    def test_zero_tolerance_disables_matching(self):
        """Tolerance of 0 prevents auto-assigning work locations."""
        self.env.company.geo_tolerance_meters = 0.0
        att = self._make_attendance(in_lat=_LAT, in_lon=_LON)
        self.assertFalse(att.in_work_location_id)

    def test_company_id_frozen_at_creation(self):
        """company_id stays fixed even if employee's company changes."""
        att = self._make_attendance(in_lat=_LAT, in_lon=_LON)
        original_company = att.company_id
        new_company = self.env["res.company"].create({"name": "Other Company"})
        self.employee.company_id = new_company
        self.assertEqual(att.company_id, original_company)
        att.invalidate_recordset()
        self.assertEqual(att.company_id, original_company)
