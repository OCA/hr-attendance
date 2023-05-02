# Copyright 2017 Odoo S.A.
# Copyright 2018 ForgeFlow, S.L.
# Copyright 2023 Tecnativa - Víctor Martínez
# License LGPL-3 - See http://www.gnu.org/licenses/lgpl-3.0.html

from datetime import datetime

from odoo.tests import common, new_test_user, users
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DF


class TestHrAttendanceReason(common.TransactionCase):
    def setUp(self):
        super().setUp()
        self.att_reason_model = self.env["hr.attendance.reason"]
        ctx = {
            "mail_create_nolog": True,
            "mail_create_nosubscribe": True,
            "mail_notrack": True,
            "no_reset_password": True,
        }
        self.user = new_test_user(
            self.env,
            login="test-user",
            groups="base.group_user,hr_attendance.group_hr_attendance",
            context=ctx,
        )
        self.employee = self.env["hr.employee"].create(
            {"name": self.user.login, "user_id": self.user.id}
        )
        self.att_reason_in = self.att_reason_model.create(
            {"name": "Bus did not come", "code": "BB", "action_type": "sign_in"}
        )
        self.att_reason_out = self.att_reason_model.create(
            {"name": "A lot of work", "code": "WORK", "action_type": "sign_out"}
        )

    @users("test-user")
    def test_employee_edit(self):
        att = self.env["hr.attendance"].create(
            {
                "employee_id": self.env.user.employee_id.id,
                "check_in": datetime.now().strftime(DF),
            }
        )
        att.write({"attendance_reason_ids": [(4, self.att_reason_in.id)]})
        self.assertEqual(
            att.attendance_reason_ids.ids,
            self.att_reason_in.ids,
            "Bad Attendance Reason",
        )
        self.env.user.employee_id._attendance_action_change()

    @users("test-user")
    def test_user_attendance_manual(self):
        # check in
        res = self.env.user.employee_id.with_context(
            attendance_reason_id=self.att_reason_in.id
        ).attendance_manual({})
        self.assertIn(
            self.att_reason_in.id, res["action"]["attendance"]["attendance_reason_ids"]
        )
        # check out
        res = self.env.user.employee_id.with_context(
            attendance_reason_id=self.att_reason_out.id
        ).attendance_manual({})
        self.assertIn(
            self.att_reason_out.id, res["action"]["attendance"]["attendance_reason_ids"]
        )
