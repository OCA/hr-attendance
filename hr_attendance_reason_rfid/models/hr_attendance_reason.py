# Copyright (C) 2021 thingsintouch.com
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models

class HrAttendanceReason(models.Model):

    _inherit = "hr.attendance.reason"

    rfid_reason_ids = fields.One2many(
        "hr.attendance.reason.rfid",
        "reason_id",
        string="RFIDs Cards",
        help="Specifies which RFID card code are associated with this reason",
        )
