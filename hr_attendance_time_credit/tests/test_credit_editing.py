# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from datetime import datetime

from odoo.exceptions import AccessError, UserError
from odoo.tests.common import new_test_user, tagged

from .common import TestHrAttendanceTimeCreditCommon


@tagged("post_install", "-at_install")
class TestCreditEditing(TestHrAttendanceTimeCreditCommon):
    """Who may edit a credit line, and what a lock does to it."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._make_rule("Rule - 20min", minutes_fixed=20, sequence=10)
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
        # The officer owns this employee, which is what the record rule grants on.
        cls.employee.attendance_manager_id = cls.officer

    def _credit_vals(self):
        return {
            "attendance_id": self.attendance.id,
            "type_id": self.credit_type.id,
            "minutes": 5,
        }

    def _credit(self):
        return self.attendance.time_credit_ids[0]

    def test_employee_reads_own_credits_but_cannot_edit(self):
        credit = self._credit()
        self.assertTrue(credit.with_user(self.employee_user).read(["minutes"]))
        Credit = self.env["hr.attendance.time.credit"].with_user(self.employee_user)
        with self.assertRaises(AccessError):
            Credit.create(self._credit_vals())
        with self.assertRaises(AccessError):
            credit.with_user(self.employee_user).write({"minutes": 1})
        with self.assertRaises(AccessError):
            credit.with_user(self.employee_user).unlink()

    def test_officer_of_the_employee_can_edit(self):
        credit = self._credit()
        credit.with_user(self.officer).write({"minutes": 30})
        self.assertEqual(credit.minutes, 30)
        new = (
            self.env["hr.attendance.time.credit"]
            .with_user(self.officer)
            .create(self._credit_vals())
        )
        self.assertTrue(new.exists())
        new.with_user(self.officer).unlink()
        self.assertFalse(new.exists())

    def test_manager_can_edit(self):
        credit = self._credit()
        credit.with_user(self.manager).write({"minutes": 30})
        self.assertEqual(credit.minutes, 30)
        new = (
            self.env["hr.attendance.time.credit"]
            .with_user(self.manager)
            .create(self._credit_vals())
        )
        self.assertTrue(new.exists())
        new.with_user(self.manager).unlink()
        self.assertFalse(new.exists())

    def test_locked_refuses_create_write_and_unlink(self):
        """The lock stops even a manager, not only an employee."""
        self.attendance.write({"credit_locked": True})
        credit = self._credit()
        Credit = self.env["hr.attendance.time.credit"].with_user(self.manager)
        with self.assertRaises(UserError):
            Credit.create(self._credit_vals())
        with self.assertRaises(UserError):
            credit.with_user(self.manager).write({"minutes": 1})
        with self.assertRaises(UserError):
            credit.with_user(self.manager).unlink()

    def test_deleting_a_locked_attendance_still_cascades(self):
        self.attendance.write({"credit_locked": True})
        credit_ids = self.attendance.time_credit_ids.ids
        self.attendance.unlink()
        self.assertFalse(
            self.env["hr.attendance.time.credit"].browse(credit_ids).exists()
        )

    def test_manual_line_defaults_and_survives_a_recompute(self):
        manual = self.env["hr.attendance.time.credit"].create(self._credit_vals())
        self.assertEqual(manual.origin, "manual")
        self.attendance.write({"check_out": datetime(2026, 1, 7, 17, 0, 0)})
        self.assertTrue(manual.exists())
        self.assertEqual(manual.origin, "manual")
        engine_lines = self.attendance.time_credit_ids.filtered("rule_id")
        self.assertTrue(engine_lines)
        self.assertEqual(set(engine_lines.mapped("origin")), {"automatic"})
