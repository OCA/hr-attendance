# Copyright 2017 Odoo S.A.
# Copyright 2018 ForgeFlow, S.L.
# License LGPL-3 - See http://www.gnu.org/licenses/lgpl-3.0.html

from odoo import Command, fields, models


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    attendance_reason_ids = fields.Many2many(
        comodel_name="hr.attendance.reason",
        string="Attendance Reason",
        help="Specifies the reason for signing In/signing Out in case of "
        "less or extra hours.",
    )

    def _cron_absence_detection(self):
        reason = self.env.company.sudo().reason_for_attendance_absence_detection
        return super(
            HrAttendance,
            self.with_context(default_attendance_reason_ids=[Command.link(reason.id)]),
        )._cron_absence_detection()
