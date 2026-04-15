# Copyright 2026 - Luis Burrel - nurzeit.de
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class HrEmployeeBase(models.AbstractModel):

    _inherit = "hr.employee.base"

    @api.model
    def register_attendance(self, card_code, log=False, timestamp=False, **kwargs):
        """
        Overrides core method to accept an explicit timestamp for RFID logs.
        Uses context injection to pass the time to the hr.attendance model safely.
        """
        action_self = self
        if timestamp:
            action_self = self.with_context(rfid_custom_time=timestamp)

        res = super(HrEmployeeBase, action_self).register_attendance(
            card_code, **kwargs
        )

        new_log = self._prepare_attendance_rfid_log(res)
        if log:
            log.sudo().write(new_log)
        else:
            self.env["hr.attendance.rfid.log"].create(new_log)

        res["in_rfid_log"] = True
        return res

    def _prepare_attendance_rfid_log(self, res):
        custom_time = self.env.context.get("rfid_custom_time")
        vals = {
            "state": "success" if res.get("logged") else "failed",
            "rfid_card_code": res.get("rfid_card_code"),
            "employee_name": res.get("employee_name"),
            "employee_id": res.get("employee_id"),
            "error_message": res.get("error_message"),
            "logged": res.get("logged"),
            "action": res.get("action"),
            "timestamp": custom_time or fields.Datetime.now(),
        }
        return vals

    @api.model
    def register_attendance_with_log(self, log):
        result = self.register_attendance(
            log.rfid_card_code, log=log, timestamp=log.timestamp
        )
        return result
