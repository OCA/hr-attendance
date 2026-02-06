# Copyright 2021 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date

import freezegun

from odoo.tests import new_test_user, users

from odoo.addons.base.tests.common import BaseCommon


class TestHRBirthdayWelcomeMessage(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = new_test_user(
            cls.env,
            login="test-user",
            groups="base.group_user,hr_attendance.group_hr_attendance_own_reader",
        )
        cls.employee = cls.env["hr.employee"].create(
            {
                "name": cls.user.login,
                "user_id": cls.user.id,
                "birthday": date(2002, 1, 12),
            }
        )

    @users("test-user")
    def test_attendance_action_is_birthday(self):
        with freezegun.freeze_time("2020-01-12"):
            result = self.env.user.employee_id._attendance_action_change({})
            self.assertTrue("is_birthday" in result["action"])
            self.assertTrue(result["action"]["is_birthday"])

    @users("test-user")
    def test_attendance_action_is_not_birthday(self):
        with freezegun.freeze_time("2020-01-14"):
            result = self.env.user.employee_id._attendance_action_change({})
            self.assertFalse("is_birthday" in result["action"])
