# Copyright (C) 2021 thingsintouch.com
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models

class HrAttendanceReasonRFID(models.Model):
    _name = "hr.attendance.reason.rfid"
    _description = "RFIDs for Attendance Reasons"
    
    _sql_constraints = [
        (
            "rfid_code_uniq",
            "UNIQUE(rfid_code)",
            "The rfid code should be unique.",
        )
    ]

    rfid_code = fields.Char("RFID Reason Card Code", copy=False)

    reason_id = fields.Many2one(
        comodel_name="hr.attendance.reason",
        string="Attendance Reason",
        help="Specifies the reason assigned to the RFID card code",
    )

