from odoo.tests.common import TransactionCase


class TestGeolocationAttendance(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.location = cls.env["hr.attendance.location"].create(
            {
                "name": "Central Office",
                "latitude": 40.416775,
                "longitude": -3.703790,
                "radius_m": 200,
            }
        )

        cls.employee = cls.env["hr.employee"].create(
            {
                "name": "Test Employee",
            }
        )

    def test_employee_inside_zone(self):
        ok, zone = self.employee._is_inside_any_allowed_location(40.416800, -3.703800)
        self.assertTrue(ok, "Should allow attendance inside the zone")
        self.assertEqual(zone, self.location)

    def test_employee_outside_zone(self):
        ok, zone = self.employee._is_inside_any_allowed_location(41.0, -3.7)
        self.assertFalse(ok, "Should not allow attendance outside the zone")

    def test_bypass_geolocation(self):
        self.employee.bypass_geolocation_check = True
        ok, zone = self.employee._is_inside_any_allowed_location(41.0, -3.7)
        self.assertTrue(ok, "Employee with bypass should be allowed anywhere")
