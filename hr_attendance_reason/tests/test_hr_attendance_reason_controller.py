# License LGPL-3 - See http://www.gnu.org/licenses/lgpl-3.0.html

from odoo.tests import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestHrAttendanceReasonController(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.attendance_kiosk_use_pin = False
        cls.reason_in = cls.env["hr.attendance.reason"].create(
            {
                "name": "Visit customer",
                "code": "VC",
                "action_type": "sign_in",
                "show_on_attendance_screen": True,
            }
        )
        cls.reason_out = cls.env["hr.attendance.reason"].create(
            {
                "name": "Felt sick",
                "code": "FS",
                "action_type": "sign_out",
                "show_on_attendance_screen": True,
            }
        )
        cls.company.write(
            {
                "show_reason_on_attendance_screen": True,
                "reason_on_attendance_screen_default_sign_in": cls.reason_in.id,
            }
        )
        cls.user = cls.env["res.users"].create(
            {
                "name": "Reason user",
                "login": "reason_user",
                "password": "reason_user",
                "group_ids": [(6, 0, [cls.env.ref("base.group_user").id])],
            }
        )
        cls.employee = cls.env["hr.employee"].create(
            {"name": "Reason employee", "user_id": cls.user.id}
        )

    def test_systray_with_reason(self):
        self.authenticate("reason_user", "reason_user")
        data = self.make_jsonrpc_request("/hr_attendance/attendance_user_data", {})
        self.assertTrue(data["show_reason_on_attendance_screen"])
        self.assertEqual(data["default_sign_in_reason_id"], self.reason_in.id)
        self.assertEqual([r["id"] for r in data["reasons"]], [self.reason_in.id])
        self.make_jsonrpc_request(
            "/hr_attendance/systray_check_in_out",
            {"attendance_reason_id": str(self.reason_in.id)},
        )
        attendance = self.employee.last_attendance_id
        self.assertEqual(attendance.attendance_reason_ids, self.reason_in)
        data = self.make_jsonrpc_request("/hr_attendance/attendance_user_data", {})
        self.assertEqual([r["id"] for r in data["reasons"]], [self.reason_out.id])
        # Empty reason (as sent by the systray when none is selected)
        self.make_jsonrpc_request(
            "/hr_attendance/systray_check_in_out", {"attendance_reason_id": ""}
        )
        self.assertTrue(attendance.check_out)
        self.assertEqual(attendance.attendance_reason_ids, self.reason_in)

    def test_invalid_reason_is_ignored(self):
        other_company = self.env["res.company"].create({"name": "Other company"})
        foreign_reason = self.env["hr.attendance.reason"].create(
            {
                "name": "Foreign",
                "code": "FO",
                "action_type": "sign_in",
                "show_on_attendance_screen": True,
                "company_id": other_company.id,
            }
        )
        self.authenticate("reason_user", "reason_user")
        # Wrong type (sign_out reason on a check in), other company, not a number
        for bad_id in (self.reason_out.id, foreign_reason.id, "abc"):
            self.make_jsonrpc_request(
                "/hr_attendance/systray_check_in_out",
                {"attendance_reason_id": str(bad_id)},
            )
            attendance = self.employee.last_attendance_id
            self.assertFalse(attendance.attendance_reason_ids)
            attendance.sudo().unlink()
        # A sign in reason is not valid to check out
        self.make_jsonrpc_request("/hr_attendance/systray_check_in_out", {})
        self.make_jsonrpc_request(
            "/hr_attendance/systray_check_in_out",
            {"attendance_reason_id": str(self.reason_in.id)},
        )
        attendance = self.employee.last_attendance_id
        self.assertTrue(attendance.check_out)
        self.assertFalse(attendance.attendance_reason_ids)

    def test_kiosk_with_reason(self):
        token = self.company.attendance_kiosk_key
        settings = self.make_jsonrpc_request(
            "/hr_attendance_reason/reason_settings", {"token": token}
        )
        self.assertTrue(settings["show_reason_on_attendance_screen"])
        res = self.make_jsonrpc_request(
            "/hr_attendance_reason/get_reasons",
            {"token": token, "employee_id": self.employee.id, "pin_code": False},
        )
        self.assertEqual([r["id"] for r in res["reasons"]], [self.reason_in.id])
        self.make_jsonrpc_request(
            "/hr_attendance/manual_selection",
            {
                "token": token,
                "employee_id": self.employee.id,
                "pin_code": False,
                "attendance_reason_id": str(self.reason_in.id),
            },
        )
        self.assertEqual(
            self.employee.last_attendance_id.attendance_reason_ids, self.reason_in
        )
        res = self.make_jsonrpc_request(
            "/hr_attendance_reason/get_reasons",
            {"token": token, "employee_id": self.employee.id, "pin_code": False},
        )
        self.assertEqual([r["id"] for r in res["reasons"]], [self.reason_out.id])
        # Wrong token returns nothing
        self.assertFalse(
            self.make_jsonrpc_request(
                "/hr_attendance_reason/get_reasons",
                {"token": "wrong", "employee_id": self.employee.id, "pin_code": False},
            )
        )
