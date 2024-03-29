# Copyright 2018-19 ForgeFlow S.L. (https://www.forgeflow.com)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from datetime import datetime, timedelta
from unittest.mock import patch

from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.tools.misc import mute_logger


class TestHrAttendance(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.employee_model = cls.env["hr.employee"]
        cls.test_employee = cls.env.ref("hr.employee_al")
        cls.rfid_card_code = "5b3f5"
        cls.test_employee.rfid_card_code = cls.rfid_card_code

    def test_valid_employee(self):
        """Valid employee"""
        res = self.employee_model.register_attendance(self.rfid_card_code)
        self.assertTrue("action" in res and res["action"] == "check_in")
        self.assertTrue("logged" in res and res["logged"])
        self.assertTrue(
            "rfid_card_code" in res and res["rfid_card_code"] == self.rfid_card_code
        )
        res = self.employee_model.register_attendance(self.rfid_card_code)
        self.assertTrue("action" in res and res["action"] == "check_out")
        self.assertTrue("logged" in res and res["logged"])

    @mute_logger("odoo.addons.hr_attendance_rfid.models.hr_employee")
    def test_exception_code(self):
        """Checkout is created for a future datetime"""
        self.env["hr.attendance"].create(
            {
                "employee_id": self.test_employee.id,
                "check_in": fields.Date.today(),
                "check_out": fields.Datetime.to_string(
                    datetime.today() + timedelta(hours=8)
                ),
            }
        )
        self.test_employee.update({"attendance_state": "checked_in"})
        res = self.employee_model.register_attendance(self.rfid_card_code)
        self.assertNotEqual(res["error_message"], "")

    def test_invalid_code(self):
        """Invalid employee"""
        invalid_code = "029238d"
        res = self.employee_model.register_attendance(invalid_code)
        self.assertTrue("action" in res and res["action"] == "FALSE")
        self.assertTrue("logged" in res and not res["logged"])
        self.assertTrue(
            "rfid_card_code" in res and res["rfid_card_code"] == invalid_code
        )

    @mute_logger("odoo.addons.hr_attendance_rfid.models.hr_employee")
    def test_no_attendance_recorded(self):
        """No record found to record the attendance"""
        with patch(
            "odoo.addons.hr_attendance.models.hr_employee.HrEmployee._attendance_action_change"
        ) as attendance_action_change_returns_none:
            attendance_action_change_returns_none.return_value = None
            res = self.employee_model.register_attendance(self.rfid_card_code)
            self.assertNotEqual(res["error_message"], "")
