# Copyright 2023 - thingsintouch.com
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, api, models, fields
from datetime import datetime

import freezegun


class HrEmployeeBase(models.AbstractModel):

    _inherit = "hr.employee.base"

    @api.model
    def register_attendance(self, card_code, log= False):
        res = super().register_attendance(card_code)
        new_log = self._prepare_attendance_rfid_log(res)
        if log:
            log.sudo().write(
                new_log
            )
        else:
            self.env["hr.attendance.rfid.log"].create(
                new_log
            )
        res["in_rfid_log"] = True
        return res

    def _prepare_attendance_rfid_log(self, res):
        return {
            "state": "success" if res["logged"] else "failed",
            "rfid_card_code": res["rfid_card_code"],
            "employee_name": res["employee_name"],
            "employee_id": res["employee_id"],
            "error_message":res["error_message"],
            "logged":res["logged"],
            "action": res["action"],
            "timestamp": fields.Datetime.now()
        }

    @api.model
    def register_attendance_with_log(self, log):
        with freezegun.freeze_time(datetime.fromtimestamp(log.timestamp.timestamp(), tz=None)):
            result = self.register_attendance(log.rfid_card_code, log)
        return result
