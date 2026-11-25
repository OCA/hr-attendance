# Copyright 2019 ForgeFlow, S.L.
# Copyright 2023 Tecnativa - Víctor Martínez
# License LGPL-3 - See http://www.gnu.org/licenses/lgpl-3.0.html

from odoo.tests.common import TransactionCase


class TestHrAttendanceGeolocation(TransactionCase):
    def setUp(self):
        super().setUp()
        self.hr_attendance_model = self.env["hr.attendance"]
        self.hr_employee_model = self.env["hr.employee"]
        self.employee = self.hr_employee_model.create({"name": "Employee A"})
        self.location = ("41.3910970", "2.1548569")

    def test_attendance_geolocation(self):
        latitude, longitude = map(float, self.location)
        self.employee._attendance_action_change(
            {
                "latitude": latitude,
                "longitude": longitude,
                "mode": "manual",
            }
        )
        attendances = self.hr_attendance_model.search(
            [("employee_id", "=", self.employee.id)]
        )
        self.assertEqual(len(attendances), 1, "One attendance should have been created")
        self.assertAlmostEqual(attendances[0].check_in_latitude, latitude, places=7)
        self.assertAlmostEqual(attendances[0].check_in_longitude, longitude, places=7)
        self.assertTrue(attendances[0].check_in_latitude_text)
        self.assertTrue(attendances[0].check_in_longitude_text)

        self.employee._attendance_action_change(
            {
                "latitude": latitude,
                "longitude": longitude,
                "mode": "manual",
            }
        )
        self.assertAlmostEqual(attendances[0].check_out_latitude, latitude, places=7)
        self.assertAlmostEqual(attendances[0].check_out_longitude, longitude, places=7)
        self.assertTrue(attendances[0].check_out_latitude_text)
        self.assertTrue(attendances[0].check_out_longitude_text)
