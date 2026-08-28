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
    net_worked_hours = fields.Float(
        compute="_compute_break_hours",
        store=True,
        aggregator="sum",
        help="Worked hours minus the recorded breaks.",
    )
    is_on_break = fields.Boolean(
        string="On Break",
        compute="_compute_is_on_break",
        help="The employee currently has an open (running) break.",
    )

    @api.depends("break_ids.duration", "worked_hours")
    def _compute_break_hours(self):
        for attendance in self:
            attendance.break_hours = sum(attendance.break_ids.mapped("duration"))
            attendance.net_worked_hours = max(
                0.0, attendance.worked_hours - attendance.break_hours
            )

    @api.depends("break_ids.break_stop")
    def _compute_is_on_break(self):
        for attendance in self:
            attendance.is_on_break = any(not b.break_stop for b in attendance.break_ids)

    def _get_open_break(self):
        self.ensure_one()
        return self.break_ids.filtered(lambda b: not b.break_stop)[:1]

    def _close_open_breaks(self, stop_dt=None):
        """Close any running break, e.g. when the attendance is checked out."""
        stop_dt = stop_dt or fields.Datetime.now()
        for attendance in self:
            open_breaks = attendance.break_ids.filtered(lambda b: not b.break_stop)
            open_breaks.write({"break_stop": stop_dt})

    def toggle_break(self):
        """Start a break if none is running, otherwise end the running one.

        Returns ``True`` when the employee ends up on a break, ``False`` when the
        break has just been closed.
        """
        self.ensure_one()
        open_break = self._get_open_break()
        if open_break:
            open_break.break_stop = fields.Datetime.now()
            return False
        self.env["hr.attendance.break"].create(
            {"attendance_id": self.id, "break_start": fields.Datetime.now()}
        )
        return True
