# © 2023 initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import TransactionCase


class TestAttendance(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.employee = cls.env["hr.employee"].create(
            {
                "name": "Test Employee",
                "user_id": cls.env.user.id,
                "company_id": cls.env.company.id,
                "tz": "UTC",
            }
        )
        cls.reason = cls.env["hr.attendance.reason"].create(
            {
                "name": "Missing Attendance",
                "code": "MA",
            }
        )

    def test_attendance_creation_no_reason(self):
        self.env.company.attendance_missing_days_reason = False
        attendances_before = self.employee.attendance_ids
        self.employee._create_missing_attendances()
        attendances_after = self.employee.attendance_ids

        self.assertEqual(attendances_before, attendances_after)

    def test_attendance_creation_with_reason(self):
        self.env.company.attendance_missing_days_reason = self.reason
        attendances_before = self.employee.attendance_ids
        self.employee._create_missing_attendances()
        attendances_after = self.employee.attendance_ids

        attendances_new = attendances_after - attendances_before
        self.assertTrue(attendances_new)
        self.assertFalse(any(attendances_new.mapped("worked_hours")))
