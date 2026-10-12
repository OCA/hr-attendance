# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime

import psycopg2

from odoo import Command
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, tagged
from odoo.tools import mute_logger


@tagged("post_install", "-at_install")
class TestHrAttendanceRestTime(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("base.main_company")
        cls.calendar = cls.env["resource.calendar"].create(
            {
                "name": "Flex Calendar",
                "company_id": cls.company.id,
                "flexible_hours": True,
                "hours_per_day": 8,
                "full_time_required_hours": 40,
                "rest_time_rule_ids": [
                    Command.create({"min_hours": 4.0, "rest_time": 0.25}),
                    Command.create({"min_hours": 6.0, "rest_time": 0.5}),
                    Command.create({"min_hours": 8.0, "rest_time": 1.0}),
                ],
            }
        )
        cls.employee = cls.env["hr.employee"].create(
            {
                "name": "Test Employee",
                "company_id": cls.company.id,
                "resource_calendar_id": cls.calendar.id,
            }
        )

    def _create_attendance(self, employee=None, check_in=None, check_out=None):
        return self.env["hr.attendance"].create(
            {
                "employee_id": (employee or self.employee).id,
                "check_in": check_in or datetime(2025, 1, 6, 8, 0),
                "check_out": check_out,
            }
        )

    def _create_user_with_groups(self, name, login, group_xmlids):
        return self.env["res.users"].create(
            {
                "name": name,
                "login": login,
                "groups_id": [
                    Command.set([self.env.ref(xmlid).id for xmlid in group_xmlids])
                ],
            }
        )

    def test_rest_time_rule_matching(self):
        """Rest time rules match by highest min_hours threshold (>= comparison)."""
        cases = [
            (datetime(2025, 1, 6, 8, 0), datetime(2025, 1, 6, 11, 0), 0.0, "3h"),
            (datetime(2025, 1, 7, 8, 0), datetime(2025, 1, 7, 11, 59), 0.0, "3.98h"),
            (datetime(2025, 1, 8, 8, 0), datetime(2025, 1, 8, 12, 0), 0.25, "4h"),
            (datetime(2025, 1, 9, 8, 0), datetime(2025, 1, 9, 13, 0), 0.25, "5h"),
            (datetime(2025, 1, 10, 8, 0), datetime(2025, 1, 10, 14, 0), 0.5, "6h"),
            (datetime(2025, 1, 13, 8, 0), datetime(2025, 1, 13, 15, 0), 0.5, "7h"),
            (datetime(2025, 1, 14, 8, 0), datetime(2025, 1, 14, 16, 0), 1.0, "8h"),
            (datetime(2025, 1, 15, 8, 0), datetime(2025, 1, 15, 17, 0), 1.0, "9h"),
        ]
        for check_in, check_out, expected_rest, desc in cases:
            att = self._create_attendance(check_in=check_in, check_out=check_out)
            self.assertEqual(att.rest_time, expected_rest, desc)

    def test_constraint_negative_values(self):
        with self.assertRaises(ValidationError):
            self.env["resource.calendar.rest.time.rule"].create(
                {"calendar_id": self.calendar.id, "min_hours": 10.0, "rest_time": -0.5}
            )
        with self.assertRaises(ValidationError):
            self.env["resource.calendar.rest.time.rule"].create(
                {"calendar_id": self.calendar.id, "min_hours": -2.0, "rest_time": 0.5}
            )

    def test_constraint_unique_min_hours_per_calendar(self):
        with (
            self.assertRaises(psycopg2.IntegrityError),
            mute_logger("odoo.sql_db"),
        ):
            self.env["resource.calendar.rest.time.rule"].create(
                {"calendar_id": self.calendar.id, "min_hours": 6.0, "rest_time": 0.75}
            )

    def test_unique_min_hours_across_calendars(self):
        """Same min_hours is allowed on different calendars."""
        other_calendar = self.env["resource.calendar"].create(
            {
                "name": "Other Calendar",
                "company_id": self.company.id,
                "flexible_hours": True,
            }
        )
        rule = self.env["resource.calendar.rest.time.rule"].create(
            {"calendar_id": other_calendar.id, "min_hours": 6.0, "rest_time": 0.5}
        )
        self.assertTrue(rule)

    def test_worked_hours_deducts_rest_time(self):
        """worked_hours = gross hours - rest_time."""
        att = self._create_attendance(check_out=datetime(2025, 1, 6, 17, 0))
        self.assertEqual(att.rest_time, 1.0)
        self.assertEqual(att.worked_hours, 8.0)

    def test_manual_override(self):
        att = self._create_attendance(check_out=datetime(2025, 1, 6, 17, 0))
        att.rest_time = 0.5
        self.assertEqual(att.worked_hours, 8.5)

    def test_open_attendance(self):
        """Open attendance (no check_out) has 0.0 rest_time."""
        att = self._create_attendance()
        self.assertEqual(att.rest_time, 0.0)

    def test_non_flexible_calendar(self):
        """Non-flexible calendar does not apply rest time rules."""
        non_flex_calendar = self.env["resource.calendar"].create(
            {
                "name": "Standard Calendar",
                "company_id": self.company.id,
                "flexible_hours": False,
                "attendance_ids": [
                    Command.create(
                        {
                            "name": "Monday",
                            "dayofweek": "0",
                            "hour_from": 8.0,
                            "hour_to": 17.0,
                            "day_period": "morning",
                        }
                    ),
                ],
            }
        )
        non_flex_employee = self.env["hr.employee"].create(
            {
                "name": "Standard Employee",
                "company_id": self.company.id,
                "resource_calendar_id": non_flex_calendar.id,
            }
        )
        att = self._create_attendance(
            employee=non_flex_employee, check_out=datetime(2025, 1, 6, 17, 0)
        )
        self.assertEqual(att.rest_time, 0.0)

    def test_overtime_reflects_rest_time_deduction(self):
        """Overtime is computed on net hours (gross - rest_time)."""
        # 10 gross hours on a day with 8h planned -> 2h overtime without rest
        # With rest_time=1.0 (rule for >=8h), net=9h -> 1h overtime
        att = self._create_attendance(
            check_in=datetime(2025, 1, 6, 8, 0), check_out=datetime(2025, 1, 6, 18, 0)
        )
        self.assertEqual(att.rest_time, 1.0)
        overtime = self.env["hr.attendance.overtime"].search(
            [("employee_id", "=", self.employee.id), ("date", "=", "2025-01-06")]
        )
        self.assertEqual(len(overtime), 1)
        self.assertEqual(overtime.duration, 1.0)

    def test_constraint_rest_time_exceeds_gross(self):
        att = self._create_attendance(check_out=datetime(2025, 1, 6, 10, 0))
        with self.assertRaises(ValidationError):
            att.rest_time = 3.0

    def test_is_rest_time_editable_manager(self):
        """Manager can always edit rest_time."""
        manager = self._create_user_with_groups(
            "Manager",
            "manager",
            ["base.group_user", "hr_attendance.group_hr_attendance_manager"],
        )
        att = self._create_attendance(check_out=datetime(2025, 1, 6, 17, 0))
        self.assertTrue(att.with_user(manager).is_rest_time_editable)

    def test_is_rest_time_editable_officer(self):
        """Officer can edit rest_time only for managed employees."""
        officer = self._create_user_with_groups(
            "Officer",
            "officer",
            ["base.group_user", "hr_attendance.group_hr_attendance_officer"],
        )
        att = self._create_attendance(check_out=datetime(2025, 1, 6, 17, 0))
        self.assertFalse(att.with_user(officer).is_rest_time_editable)
        self.employee.attendance_manager_id = officer
        self.assertTrue(att.with_user(officer).is_rest_time_editable)

    def test_is_rest_time_editable_user(self):
        """Regular user can edit rest_time only when overtime is not approved."""
        user = self._create_user_with_groups("User", "user", ["base.group_user"])
        att = self._create_attendance(check_out=datetime(2025, 1, 6, 17, 0))
        att.overtime_status = "approved"
        self.assertFalse(att.with_user(user).is_rest_time_editable)
        att.overtime_status = False
        self.assertTrue(att.with_user(user).is_rest_time_editable)
