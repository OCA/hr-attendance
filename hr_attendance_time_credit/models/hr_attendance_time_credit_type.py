# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models

from .hr_attendance_time_credit_rule import SEGMENT_MODE_SELECTION


class HrAttendanceTimeCreditType(models.Model):
    _name = "hr.attendance.time.credit.type"
    _description = "Attendance Time Credit Type"

    name = fields.Char(
        required=True,
        translate=True,
        help="Human-readable label for this credit type, "
        "e.g. 'Travel Time', 'Dressing Time', 'Paid Break', 'Sunday Premium'.",
    )
    code = fields.Char(
        required=True,
        help="Short unique identifier for this credit type, e.g. 'travel', "
        "'sunday_premium', 'holiday_surcharge'. Must be unique per company.",
    )
    active = fields.Boolean(
        default=True,
        help="If unchecked, this credit type will be hidden and unavailable for "
        "new rules.",
    )
    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
        help="Company that owns this credit type.",
    )
    segment_mode = fields.Selection(
        SEGMENT_MODE_SELECTION,
        default="segment",
        help="Default mode for rules of this type. 'Segmented' evaluates each "
        "calendar-day segment independently (current default). 'Consolidated' "
        "produces one credit line per attendance for midnight-crossing "
        "attendances.",
    )

    _sql_constraints = [
        (
            "code_company_uniq",
            "unique(code, company_id)",
            "The code must be unique per company.",
        ),
    ]
