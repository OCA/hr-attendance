# Copyright 2021 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date

import freezegun

from odoo.tests import TransactionCase


class TestHRBirthdayWelcomeMessage(TransactionCase):
    def setUp(self):
        super().setUp()
        self.user = (
            self.env["res.users"]
            .sudo()
            .create(
                {
                    "name": "Test User",
                    "login": "user@test.com",
                    "email": "user@test.com",
                    "groups_id": [(4, self.env.ref("base.group_user").id)],
                }
            )
        )

        self.Employee = self.env["hr.employee"]
        self.EmployeePublic = self.env["hr.employee.public"]
        self.SudoEmployee = self.Employee.sudo()
        self.employee = self.SudoEmployee.create(
            {
                "name": "Employee Test",
                "user_id": self.user.id,
                "birthday": date(2002, 1, 12),
            }
        )

    def test_attendance_action_is_birthday(self):
        with freezegun.freeze_time("2020-01-12"):
            result = self.employee.with_user(self.user).attendance_manual(
                {}, entered_pin=None
            )
            self.assertTrue("is_birthday" in result["action"])
            self.assertTrue(result["action"]["is_birthday"])

    def test_attendance_action_is_not_birthday(self):
        with freezegun.freeze_time("2020-01-14"):
            result = self.employee.with_user(self.user).attendance_manual(
                {}, entered_pin=None
            )
            self.assertFalse("is_birthday" in result["action"])
