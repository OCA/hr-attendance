# Copyright 2017 Odoo S.A.
# Copyright 2018 ForgeFlow, S.L.
# License LGPL-3 - See http://www.gnu.org/licenses/lgpl-3.0.html

from odoo import fields, models


class HrAttendance(models.Model):
    _inherit = "hr.attendance"
    _mro_pad = ["mail.thread"]

    # Override fields to add tracking
    check_in = fields.Datetime(tracking=True)
    check_out = fields.Datetime(tracking=True)

    attendance_reason_ids = fields.Many2many(
        comodel_name="hr.attendance.reason",
        string="Attendance Reason",
        help="Specifies the reason for signing In/signing Out in case of "
        "less or extra hours.",
        tracking=True,
    )
