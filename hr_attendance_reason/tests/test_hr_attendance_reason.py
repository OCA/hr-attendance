# Copyright 2017 Odoo S.A.
# Copyright 2018 ForgeFlow, S.L.
# Copyright 2023 Tecnativa - Víctor Martínez
# License LGPL-3 - See http://www.gnu.org/licenses/lgpl-3.0.html

from odoo import fields
from odoo.tests import new_test_user, users

from odoo.addons.base.tests.common import BaseCommon


class TestHrAttendanceReason(BaseCommon):
    _test_user_groups = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.att_reason_model = cls.env["hr.attendance.reason"]
        cls.user = new_test_user(
            cls.env,
            login="test-user",
            groups="base.group_user,hr_attendance.group_hr_attendance_own_reader",
        )
        cls.employee = cls.env["hr.employee"].create(
            {"name": cls.user.login, "user_id": cls.user.id}
        )
        cls.att_reason_in = cls.att_reason_model.create(
            {
                "name": "Bus did not come",
                "code": "BB",
                "action_type": "sign_in",
                "show_on_attendance_screen": True,
            }
        )
        cls.att_reason_out = cls.att_reason_model.create(
            {
                "name": "A lot of work",
                "code": "WORK",
                "action_type": "sign_out",
                "show_on_attendance_screen": True,
            }
        )

    @users("test-user")
    def test_employee_edit(self):
        self.env["hr.attendance"].sudo().create(
            {
                "employee_id": self.env.user.employee_id.id,
                "check_in": fields.Datetime.now(),
                "attendance_reason_ids": [(4, self.att_reason_in.id)],
            }
        )
        # check out
        employee = self.env.user.employee_id.with_context(
            attendance_reason_id=self.att_reason_out.id
        )
        employee._attendance_action_change({})
        attendance = employee.last_attendance_id
        self.assertTrue(attendance.check_out)
        self.assertIn(self.att_reason_in, attendance.attendance_reason_ids)
        self.assertIn(self.att_reason_out, attendance.attendance_reason_ids)

    @users("test-user")
    def test_user_attendance_manual(self):
        # check in
        employee = self.env.user.employee_id
        employee.with_context(
            attendance_reason_id=self.att_reason_in.id
        )._attendance_action_change({})
        attendance = employee.last_attendance_id
        self.assertFalse(attendance.check_out)
        self.assertIn(self.att_reason_in, attendance.attendance_reason_ids)
        # check out
        employee.with_context(
            attendance_reason_id=self.att_reason_out.id
        )._attendance_action_change({})
        self.assertEqual(attendance, employee.last_attendance_id)
        self.assertTrue(attendance.check_out)
        self.assertIn(self.att_reason_out, attendance.attendance_reason_ids)

    @users("test-user")
    def test_user_attendance_without_reason(self):
        employee = self.env.user.employee_id
        employee._attendance_action_change({})
        self.assertFalse(employee.last_attendance_id.attendance_reason_ids)
