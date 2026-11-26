# Copyright 2026 Odoo Community Association (OCA)
# License LGPL-3 - See http://www.gnu.org/licenses/lgpl-3.0.html

from odoo import api, fields, models


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    break_ids = fields.One2many(
        comodel_name="hr.attendance.break",
        inverse_name="attendance_id",
    )
    break_hours = fields.Float(
        compute="_compute_break_hours",
        store=True,
        aggregator="sum",
        help="Total break time recorded during this attendance.",
    )
    unpaid_break_hours = fields.Float(
        compute="_compute_break_hours",
        store=True,
        aggregator="sum",
        help="Unpaid break time deducted from the worked hours. Time that "
        "overlaps the lunch break of the working schedule is not deducted "
        "twice, as it is already excluded from the worked hours.",
    )
    net_worked_hours = fields.Float(
        compute="_compute_break_hours",
        store=True,
        aggregator="sum",
        help="Worked hours minus the unpaid breaks.",
    )

    @api.depends(
        "break_ids.duration",
        "break_ids.paid",
        "worked_hours",
    )
    def _compute_break_hours(self):
        for attendance in self:
            breaks = attendance.break_ids.filtered("break_stop")
            attendance.break_hours = sum(breaks.mapped("duration"))
            unpaid = 0.0
            if attendance.check_out:
                for brk in breaks.filtered(lambda b: not b.paid):
                    unpaid += brk._apply_rounding(
                        attendance._get_worked_hours_in_range(
                            brk.break_start, brk.break_stop
                        ),
                        brk.company_id.attendance_break_rounding_minutes,
                    )
            attendance.unpaid_break_hours = unpaid
            attendance.net_worked_hours = max(
                0.0, (attendance.worked_hours or 0.0) - unpaid
            )
