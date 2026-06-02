# Copyright 2026 - Luis Burrel - nurzeit.de
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from datetime import timedelta

from odoo import fields, models


class RfidAttendanceLog(models.Model):
    _name = "hr.attendance.rfid.log"
    _description = "HR Attendance RFID Logging"
    _order = "id desc"

    state = fields.Selection(
        selection=[
            ("success", "Success"),
            ("failed", "Failed"),
            ("retry", "Retry"),
            ("ignore", "Ignore"),
        ],
        string="State",
        readonly=True,
        index=True,
    )
    rfid_card_code = fields.Char(readonly=True, string="RFID Card Code", copy=False)
    employee_name = fields.Char(string="Employee Name", readonly=True)
    employee_id = fields.Many2one(
        "hr.employee", string="Employee", ondelete="cascade", index=True
    )
    error_message = fields.Char(string="Error Message", readonly=True)
    logged = fields.Boolean(string="Logged", readonly=True)
    action = fields.Selection(
        selection=[
            ("check_in", "check in"),
            ("check_out", "check out"),
            ("FALSE", "undefined"),
        ],
        string="Action",
        readonly=True,
    )
    timestamp = fields.Datetime(
        string="RFID-Timestamp", default=fields.Datetime.now, required=True
    )
    retry_counter = fields.Integer(string="Retry Counter", default=0)

    def action_open_wizard_assign_employee(self):
        action = self.env["ir.actions.act_window"].for_xml_id(
            "hr_attendance_rfid_log", "action_hr_rfid_log_assign_employee"
        )
        action["context"] = {
            "default_rfid_card_code": self.rfid_card_code,
            "default_hr_attendance_rfid_log_id": self.id,
        }
        return action

    def action_set_to_retry_state(self):
        self.sudo().state = "retry"

    def action_set_to_ignore_state(self):
        self.sudo().state = "ignore"

    def action_retry_now(self):
        if self.state == "retry":
            self.retry_counter += 1
            self.env["hr.employee"].register_attendance_with_log(self)

    def _retry_attendance_rfid_log(self):
        logs_to_retry = self.search([("state", "=", "retry")])

        for log in logs_to_retry.sudo():
            log.action_retry_now()

    def _purge_attendance_rfid_log(self):
        current_date = fields.Datetime.now()

        default_purge_period_success = 5
        default_purge_period_general = 40

        params = self.env["ir.config_parameter"].sudo()
        purge_period_success = params.get_param(
            "hr_attendance_rfid_log.purge_period_success"
        )
        purge_period_general = params.get_param(
            "hr_attendance_rfid_log.purge_period_general"
        )

        try:
            purge_period_success = (
                int(purge_period_success)
                if purge_period_success
                else default_purge_period_success
            )
            purge_period_general = (
                int(purge_period_general)
                if purge_period_general
                else default_purge_period_general
            )
        except ValueError:
            purge_period_success = default_purge_period_success
            purge_period_general = default_purge_period_general

        logs_to_purge = self.search(
            [
                "|",
                "&",
                ("state", "=", "success"),
                ("timestamp", "<", current_date - timedelta(days=purge_period_success)),
                ("timestamp", "<", current_date - timedelta(days=purge_period_general)),
            ]
        )
        logs_to_purge.unlink()
