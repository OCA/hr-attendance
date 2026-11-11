# Copyright 2018-19 ForgeFlow S.L. (https://www.forgeflow.com)
# Copyright 2023 Tecnativa - Víctor Martínez
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from datetime import timedelta

from odoo import fields
from odoo.tests import new_test_user
from odoo.tests.common import users
from odoo.tools.misc import mute_logger

from odoo.addons.base.tests.common import BaseCommon


class TestHrAttendance(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        user = new_test_user(
            cls.env,
            login="hr_attendance_rfid-user",
            groups="hr_attendance_rfid.group_hr_attendance_rfid,base.group_user",
        )
        cls.rfid_card_code = "5b3f5"
        cls.env["hr.employee"].create(
            {"user_id": user.id, "rfid_card_code": cls.rfid_card_code}
        )
        cls.employee_model = cls.env["hr.employee"]

    @users("hr_attendance_rfid-user")
    def test_valid_employee(self):
        """Valid employee"""
        self.employee_model = self.employee_model.with_user(self.env.user)
        res = self.employee_model.register_attendance(self.rfid_card_code)
        self.assertTrue("action" in res and res["action"] == "check_in")
        self.assertTrue("logged" in res and res["logged"])
        self.assertTrue(
            "rfid_card_code" in res and res["rfid_card_code"] == self.rfid_card_code
        )
        res = self.employee_model.register_attendance(self.rfid_card_code)
        self.assertTrue("action" in res and res["action"] == "check_out")
        self.assertTrue("logged" in res and res["logged"])

    @users("hr_attendance_rfid-user")
    @mute_logger("odoo.addons.hr_attendance_rfid.models.hr_employee")
    def test_exception_code(self):
        """Checkout is created for a future datetime"""
        self.employee_model = self.employee_model.with_user(self.env.user)
        employee = self.env.user.employee_id
        self.env["hr.attendance"].create(
            {
                "employee_id": employee.id,
                "check_in": fields.Date.today(),
                "check_out": fields.Datetime.to_string(
                    fields.Datetime.now() + timedelta(hours=8)
                ),
            }
        )
        employee.update({"attendance_state": "checked_in"})
        res = self.employee_model.register_attendance(self.rfid_card_code)
        self.assertNotEqual(res["error_message"], "")

    @users("hr_attendance_rfid-user")
    @mute_logger("odoo.addons.hr_attendance_rfid.models.hr_employee")
    def test_invalid_code(self):
        """Invalid employee"""
        self.employee_model = self.employee_model.with_user(self.env.user)
        invalid_code = "029238d"
        res = self.employee_model.register_attendance(invalid_code)
        self.assertTrue("action" in res and res["action"] == "FALSE")
        self.assertTrue("logged" in res and not res["logged"])
        self.assertTrue(
            "rfid_card_code" in res and res["rfid_card_code"] == invalid_code
        )

    @users("hr_attendance_rfid-user")
    @mute_logger("odoo.addons.hr_attendance_rfid.models.hr_employee")
    def test_empty_code(self):
        """Invalid employee"""
        self.employee_model = self.employee_model.with_user(self.env.user)
        invalid_code = " "
        res = self.employee_model.register_attendance(invalid_code)
        self.assertTrue("action" in res and res["action"] == "FALSE")
        self.assertTrue("logged" in res and not res["logged"])
        self.assertEqual("Card code is required.", res["error_message"])
        self.assertEqual(False, res["employee_id"])
