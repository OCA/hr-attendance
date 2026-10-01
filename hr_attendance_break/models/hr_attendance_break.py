# Copyright 2026 Odoo Community Association (OCA)
# License LGPL-3 - See http://www.gnu.org/licenses/lgpl-3.0.html

from odoo import api, fields, models


class HrAttendanceBreak(models.Model):
    _name = "hr.attendance.break"
    _description = "Attendance Break"
    _order = "break_start desc"

    attendance_id = fields.Many2one(
        comodel_name="hr.attendance",
        required=True,
        ondelete="cascade",
        index=True,
    )
    employee_id = fields.Many2one(
        related="attendance_id.employee_id",
        store=True,
        index=True,
    )
    company_id = fields.Many2one(
        related="attendance_id.employee_id.company_id",
        store=True,
    )
    break_start = fields.Datetime(
        required=True,
        default=fields.Datetime.now,
    )
    break_stop = fields.Datetime(string="Break End")
    break_type = fields.Selection(
        selection=[
            ("coffee", "Coffee"),
            ("lunch", "Lunch"),
            ("other", "Other"),
        ],
        default="other",
        required=True,
    )
    duration = fields.Float(
        compute="_compute_duration",
        store=True,
        help="Break length in hours, rounded according to the company setting.",
    )

    @api.depends(
        "break_start",
        "break_stop",
        "company_id.attendance_break_rounding_minutes",
    )
    def _compute_duration(self):
        for record in self:
            if not (record.break_start and record.break_stop):
                record.duration = 0.0
                continue
            hours = (record.break_stop - record.break_start).total_seconds() / 3600.0
            step = record.company_id.attendance_break_rounding_minutes or 0
            record.duration = self._apply_rounding(hours, step)

    @staticmethod
    def _apply_rounding(hours, step_minutes):
        """Round ``hours`` to the nearest ``step_minutes`` step (0 = no rounding)."""
        if not step_minutes:
            return hours
        step = step_minutes / 60.0
        return round(hours / step) * step
