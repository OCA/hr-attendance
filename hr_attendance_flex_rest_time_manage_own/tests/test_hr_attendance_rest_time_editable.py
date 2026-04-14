# Copyright 2026 Quartile (https://www.quartile.co)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from datetime import datetime

from odoo import Command
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestHrAttendanceRestTimeEditable(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("base.main_company")
        cls.calendar = cls.env["resource.calendar"].create(
            {
                "name": "Flex Calendar",
                "company_id": cls.company.id,
                "flexible_hours": True,
                "rest_time_rule_ids": [
                    Command.create({"min_hours": 8.0, "rest_time": 1.0}),
                ],
            }
        )
        cls.officer = cls.env["res.users"].create(
            {
                "name": "Test Officer",
                "login": "test_officer",
                "groups_id": [
                    Command.set(
                        [
                            cls.env.ref("base.group_user").id,
                            cls.env.ref("hr_attendance.group_hr_attendance_officer").id,
                            cls.env.ref(
                                "hr_attendance_manage_own.group_hr_attendance_own_manager"
                            ).id,
                        ]
                    ),
                ],
            }
        )
        cls.employee = cls.env["hr.employee"].create(
            {
                "name": "Test Employee",
                "company_id": cls.company.id,
                "resource_calendar_id": cls.calendar.id,
                "user_id": cls.officer.id,
            }
        )
        cls.employee.company_id.attendance_overtime_validation = "by_manager"

    def test_officer_own_manager_can_edit_own_rest_time(self):
        """Officer with Own Manager can edit rest time on their own records."""
        att = self.env["hr.attendance"].create(
            {
                "employee_id": self.employee.id,
                "check_in": datetime(2025, 1, 6, 8, 0),
                "check_out": datetime(2025, 1, 6, 17, 0),
            }
        )
        self.assertTrue(att.with_user(self.officer).is_rest_time_editable)

    def test_officer_own_manager_cannot_edit_when_approved(self):
        """Officer cannot edit rest time when overtime is approved."""
        att = self.env["hr.attendance"].create(
            {
                "employee_id": self.employee.id,
                "check_in": datetime(2025, 1, 6, 8, 0),
                "check_out": datetime(2025, 1, 6, 17, 0),
                "overtime_status": "approved",
            }
        )
        self.assertFalse(att.with_user(self.officer).is_rest_time_editable)
