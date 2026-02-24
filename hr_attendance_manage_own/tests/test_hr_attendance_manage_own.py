# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import Command
from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestHrAttendanceManageOwn(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = cls.env["res.users"].create(
            {
                "name": "Test User",
                "login": "test_own_manager",
                "email": "test@test.com",
            }
        )
        cls.user.groups_id = [
            Command.unlink(cls.env.ref("hr_attendance.group_hr_attendance_manager").id)
        ]
        cls.employee = cls.env["hr.employee"].create(
            {"name": "Test Employee", "user_id": cls.user.id}
        )
        # Set company to require manager approval by default
        cls.employee.company_id.attendance_overtime_validation = "by_manager"
        cls.attendance = cls.env["hr.attendance"].create(
            {
                "employee_id": cls.employee.id,
                "check_in": "2026-02-26 08:00:00",
                "check_out": "2026-02-26 17:00:00",
                "overtime_status": "to_approve",
            }
        )
        cls.own_manager_group = cls.env.ref(
            "hr_attendance_manage_own.group_hr_attendance_own_manager"
        )

    def test_create_denied_without_group(self):
        with self.assertRaises(AccessError):
            self.env["hr.attendance"].with_user(self.user).create(
                {
                    "employee_id": self.employee.id,
                    "check_in": "2026-02-27 08:00:00",
                }
            )

    def test_create_allowed(self):
        self.user.groups_id = [Command.link(self.own_manager_group.id)]
        attendance = (
            self.env["hr.attendance"]
            .with_user(self.user)
            .create(
                {
                    "employee_id": self.employee.id,
                    "check_in": "2026-02-27 08:00:00",
                }
            )
        )
        self.assertEqual(attendance.overtime_status, "to_approve")
        self.assertEqual(attendance.employee_id, self.employee)

    def test_create_denied_with_approved_status(self):
        self.user.groups_id = [Command.link(self.own_manager_group.id)]
        with self.assertRaises(AccessError):
            self.env["hr.attendance"].with_user(self.user).create(
                {
                    "employee_id": self.employee.id,
                    "check_in": "2026-02-27 08:00:00",
                    "overtime_status": "approved",
                }
            )

    def test_create_allowed_with_auto_approval(self):
        self.user.groups_id = [Command.link(self.own_manager_group.id)]
        self.employee.company_id.attendance_overtime_validation = "no_validation"
        attendance = (
            self.env["hr.attendance"]
            .with_user(self.user)
            .create(
                {
                    "employee_id": self.employee.id,
                    "check_in": "2026-02-27 08:00:00",
                }
            )
        )
        self.assertEqual(attendance.overtime_status, "approved")

    def test_write_denied_without_group(self):
        with self.assertRaises(AccessError):
            self.attendance.with_user(self.user).write(
                {"check_in": "2026-02-26 09:00:00"}
            )

    def test_write_allowed_not_approved(self):
        self.user.groups_id = [Command.link(self.own_manager_group.id)]
        self.attendance.with_user(self.user).write({"check_in": "2026-02-26 09:00:00"})
        self.assertEqual(
            self.attendance.check_in.strftime("%Y-%m-%d %H:%M:%S"),
            "2026-02-26 09:00:00",
        )

    def test_write_ignored_validated_overtime_hours(self):
        self.user.groups_id = [Command.link(self.own_manager_group.id)]
        original = self.attendance.validated_overtime_hours
        self.attendance.with_user(self.user).write({"validated_overtime_hours": 99.0})
        self.assertEqual(self.attendance.validated_overtime_hours, original)

    def test_approve_refuse_own_attendance_denied(self):
        self.user.groups_id = [Command.link(self.own_manager_group.id)]
        with self.assertRaises(AccessError):
            self.attendance.with_user(self.user).action_approve_overtime()
        with self.assertRaises(AccessError):
            self.attendance.with_user(self.user).action_refuse_overtime()

    def test_write_denied_approved(self):
        self.user.groups_id = [Command.link(self.own_manager_group.id)]
        self.attendance.overtime_status = "approved"
        with self.assertRaises(AccessError):
            self.attendance.with_user(self.user).write(
                {"check_in": "2026-02-26 11:00:00"}
            )

    def test_write_denied_refused(self):
        self.user.groups_id = [Command.link(self.own_manager_group.id)]
        self.attendance.overtime_status = "refused"
        with self.assertRaises(AccessError):
            self.attendance.with_user(self.user).write(
                {"check_in": "2026-02-26 11:00:00"}
            )

    def test_unlink_allowed_to_approve(self):
        self.user.groups_id = [Command.link(self.own_manager_group.id)]
        attendance = (
            self.env["hr.attendance"]
            .with_user(self.user)
            .create(
                {
                    "employee_id": self.employee.id,
                    "check_in": "2026-02-27 08:00:00",
                }
            )
        )
        attendance.with_user(self.user).unlink()

    def test_unlink_denied_approved(self):
        self.user.groups_id = [Command.link(self.own_manager_group.id)]
        self.attendance.overtime_status = "approved"
        with self.assertRaises(AccessError):
            self.attendance.with_user(self.user).unlink()

    def test_write_allowed_no_validation(self):
        self.user.groups_id = [Command.link(self.own_manager_group.id)]
        self.employee.company_id.attendance_overtime_validation = "no_validation"
        attendance = (
            self.env["hr.attendance"]
            .with_user(self.user)
            .create(
                {
                    "employee_id": self.employee.id,
                    "check_in": "2026-02-27 08:00:00",
                }
            )
        )
        self.assertEqual(attendance.overtime_status, "approved")
        attendance.with_user(self.user).write({"check_out": "2026-02-27 17:00:00"})
        self.assertEqual(
            attendance.check_out.strftime("%Y-%m-%d %H:%M:%S"),
            "2026-02-27 17:00:00",
        )

    def test_full_manager_bypass(self):
        manager_user = self.env["res.users"].create(
            {
                "name": "Attendance Manager",
                "login": "manager_user",
                "email": "manager@test.com",
                "groups_id": [
                    Command.link(
                        self.env.ref("hr_attendance.group_hr_attendance_manager").id
                    ),
                ],
            }
        )
        self.attendance.with_user(manager_user).action_approve_overtime()
        self.assertEqual(self.attendance.overtime_status, "approved")

    def test_write_bypass_fields_on_processed(self):
        self.user.groups_id = [Command.link(self.own_manager_group.id)]
        self.attendance.overtime_status = "approved"
        self.env["ir.config_parameter"].set_param(
            "hr_attendance_manage_own.write_bypass_fields", "check_in"
        )
        self.attendance.with_user(self.user).write({"check_in": "2026-02-26 09:00:00"})
        with self.assertRaises(AccessError):
            self.attendance.with_user(self.user).write(
                {"check_in": "2026-02-26 11:00:00", "check_out": "2026-02-26 18:00:00"}
            )

    def test_attendance_manager_bypass(self):
        officer_user = self.env["res.users"].create(
            {
                "name": "Attendance Officer",
                "login": "officer_user",
                "email": "officer@test.com",
                "groups_id": [
                    Command.link(
                        self.env.ref("hr_attendance.group_hr_attendance_officer").id
                    ),
                    Command.link(self.own_manager_group.id),
                ],
            }
        )
        self.employee.attendance_manager_id = officer_user
        attendance = (
            self.env["hr.attendance"]
            .with_user(officer_user)
            .create(
                {
                    "employee_id": self.employee.id,
                    "check_in": "2026-02-27 08:00:00",
                    "overtime_status": "approved",
                }
            )
        )
        attendance.with_user(officer_user).write(
            {"check_in": "2026-02-27 10:00:00", "check_out": "2026-02-27 18:00:00"}
        )
        self.assertEqual(
            attendance.check_in.strftime("%Y-%m-%d %H:%M:%S"),
            "2026-02-27 10:00:00",
        )
        self.assertEqual(
            attendance.check_out.strftime("%Y-%m-%d %H:%M:%S"),
            "2026-02-27 18:00:00",
        )
