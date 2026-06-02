# Copyright 2026 nurzeit.de
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class RfidLogAssignEmployee(models.TransientModel):
    _name = "hr.attendance.rfid.log.assign.employee"
    _description = "Assign an employee to a RFID card code"

    hr_attendance_rfid_log_id = fields.Many2one(
        "hr.attendance.rfid.log", string="Log", required=True
    )
    rfid_card_code = fields.Char(readonly=True, string="RFID Card Code", copy=False)
    employee_id = fields.Many2one("hr.employee", string="Employee", required=True)
    warning_message = fields.Char(string="Warning Message")

    def action_assign_employee(self):
        self.employee_id.rfid_card_code = self.rfid_card_code
        records = self.env["hr.attendance.rfid.log"].search(
            [("rfid_card_code", "=", self.rfid_card_code),]  # noqa: E231
        )
        for log in records:
            log.sudo().write(
                {"employee_id": self.employee_id.id, "state": "retry",}  # noqa: E231
            )
        return {"type": "ir.actions.act_window_close"}

    @api.onchange("employee_id")
    def on_change_employee_id(self):
        for record in self:
            if record.employee_id.rfid_card_code:
                record.warning_message = _(
                    "Employee has already a RFID card code assigned. "
                    "If you continue it will be overwritten."
                )
            else:
                record.warning_message = ""
