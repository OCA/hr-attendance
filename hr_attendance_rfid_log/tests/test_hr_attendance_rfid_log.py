# Copyright 2024 thingsintouch.com
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from datetime import datetime, timedelta

from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.tools.misc import mute_logger


class TestHrAttendance(TransactionCase):
    def setUp(self):
        super(TestHrAttendance, self).setUp()
        self.log_failed =self.env["iot.template"].create(
            {
                "state" : "failed",
                "rfid_card_code": self.rfid_card_code,
                "employee_id": self.test_employee.id,
            }
        )
        # self.employee_model = self.env["hr.employee"]
        # self.test_employee = self.browse_ref("hr.employee_al")
        # self.rfid_card_code = "5b3f5"
        # self.test_employee.rfid_card_code = self.rfid_card_code

    def test_create_log(self):
        """Valid employee"""
        res = self.employee_model.register_attendance(self.rfid_card_code)
        self.assertTrue("in_rfid_log" in res and res["in_rfid_log"])

    def _get_wizard(self):
        wizard = self.env["hr.attendance.rfid.log.assign.employee"].create({
            "rfid_card_code": self.rfid_card_code,
            # You need to provide the ID of the attendance RFID log here
            "attendance_rfid_log_id": self.id,
        })
        return wizard

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
        self.assertNotEquals(res["error_message"], "")
