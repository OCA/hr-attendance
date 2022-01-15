# Copyright (C) 2021 thingsintouch.com
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class HrEmployeeBase(models.AbstractModel):

    _inherit = "hr.employee.base"

    @api.model
    def register_attendance_with_reason(self, rfid_code_employee, rfid_code_reason):
        result = self.register_attendance(rfid_code_employee)
        if result["logged"]:
            rfid_reason = self.env["hr.attendance.reason.rfid"].search(
                [("rfid_code", "=", rfid_code_reason)], limit=1
            )
            if rfid_reason and rfid_reason.reason_id:
                employee = self.env["hr.employee"].search(
                    [("id", "=", result["employee_id"])], limit=1
                )
                last_attendance = employee.last_attendance_id
                last_attendance.write({"attendance_reason_ids": [(4, rfid_reason.reason_id.id, 0)]})
        # msg = _(f"Result for rfid_code_employee {rfid_code_employee}; rfid_code_reason {rfid_code_reason} - register_attendance_with_reason {result}")
        # _logger.warning(msg)

        return result
