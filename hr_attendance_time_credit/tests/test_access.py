# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
"""One scenario covering employee, officer and manager access to time credits."""

from odoo.exceptions import AccessError, UserError
from odoo.tests.common import new_test_user, tagged

from .common import TestHrAttendanceTimeCreditCommon


@tagged("post_install", "-at_install")
class TestAccessScenario(TestHrAttendanceTimeCreditCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._make_rule("Access rule", minutes_fixed=20, sequence=10)
        cls.attendance = cls._create_fixed_attendance(hours=8, check_in_hour=8)
        cls.manager = new_test_user(
            cls.env,
            "credit_manager",
            groups="base.group_user,hr.group_hr_user,"
            "hr_attendance.group_hr_attendance_manager",
            company_ids=[(6, 0, [cls.company.id])],
        )
        cls.officer = new_test_user(
            cls.env,
            "credit_officer",
            groups="base.group_user,hr.group_hr_user,"
            "hr_attendance.group_hr_attendance_officer",
            company_ids=[(6, 0, [cls.company.id])],
        )
        cls.employee_user = new_test_user(
            cls.env,
            "credit_employee",
            groups="base.group_user",
            company_ids=[(6, 0, [cls.company.id])],
        )
        cls.employee.user_id = cls.employee_user
        cls.employee.attendance_manager_id = cls.officer

    def _credit_vals(self):
        return {
            "attendance_id": self.attendance.id,
            "type_id": self.credit_type.id,
            "minutes": 5,
        }

    def test_access_scenario(self):
        credit = self.attendance.time_credit_ids[0]

        # An employee may read their own credits but never write them.
        self.assertTrue(credit.with_user(self.employee_user).read(["minutes"]))
        Credit = self.env["hr.attendance.time.credit"].with_user(self.employee_user)
        with self.assertRaises(AccessError):
            Credit.create(self._credit_vals())
        with self.assertRaises(AccessError):
            credit.with_user(self.employee_user).write({"minutes": 1})
        with self.assertRaises(AccessError):
            credit.with_user(self.employee_user).unlink()

        # The officer responsible for the employee may edit credits and can
        # still close the attendance: the manager-only flags are read with
        # sudo inside the engine.
        credit.with_user(self.officer).write({"minutes": 30})
        self.assertEqual(credit.minutes, 30)
        new_officer_credit = (
            self.env["hr.attendance.time.credit"]
            .with_user(self.officer)
            .create(self._credit_vals())
        )
        self.assertTrue(new_officer_credit.exists())
        new_officer_credit.with_user(self.officer).unlink()
        self.assertFalse(new_officer_credit.exists())
        officer_attendance = self.attendance.with_user(self.officer)
        officer_attendance.write({"check_out": "2026-01-07 18:00:00"})
        engine_lines = officer_attendance.sudo().time_credit_ids.filtered("rule_id")
        self.assertEqual(engine_lines.minutes, 20)

        # A manager has the same editing rights without owning the employee.
        # Re-read the line: closing the attendance replaced the automatic one.
        credit = engine_lines[0]
        credit.with_user(self.manager).write({"minutes": 45})
        self.assertEqual(credit.minutes, 45)
        new_manager_credit = (
            self.env["hr.attendance.time.credit"]
            .with_user(self.manager)
            .create(self._credit_vals())
        )
        self.assertTrue(new_manager_credit.exists())
        new_manager_credit.with_user(self.manager).unlink()
        self.assertFalse(new_manager_credit.exists())

        # A credit lock overrides all of those permissions.
        self.attendance.write({"credit_locked": True})
        locked = self.env["hr.attendance.time.credit"].with_user(self.manager)
        with self.assertRaises(UserError):
            locked.create(self._credit_vals())
        with self.assertRaises(UserError):
            credit.with_user(self.manager).write({"minutes": 1})
        with self.assertRaises(UserError):
            credit.with_user(self.manager).unlink()
