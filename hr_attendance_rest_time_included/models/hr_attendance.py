# Copyright 2025 Tecnativa - Eduardo Ezerouali
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import api, fields, models


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    rest_time_ids = fields.One2many(
        comodel_name="hr.attendance.rest_time",
        inverse_name="attendance_id",
    )
    rest_hours = fields.Float(compute="_compute_rest_time", store=True, readonly=True)
    rest_time_count = fields.Integer(
        string="Break Count", compute="_compute_rest_time_count"
    )

    @api.depends("rest_time_ids.check_out")
    def _compute_rest_time(self):
        for record in self:
            record.rest_hours = sum(record.rest_time_ids.mapped("worked_hours"))

    @api.depends("rest_time_ids")
    def _compute_rest_time_count(self):
        for record in self:
            record.rest_time_count = len(record.rest_time_ids)

    def action_view_rest_times(self):
        self.ensure_one()
        return {
            "name": "Break Times",
            "type": "ir.actions.act_window",
            "res_model": "hr.attendance.rest_time",
            "view_mode": "list,form",
            "domain": [("id", "in", self.rest_time_ids.ids)],
            "context": {"default_attendance_id": self.id},
        }
