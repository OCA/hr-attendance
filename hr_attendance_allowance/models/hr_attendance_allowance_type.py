# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class HrAttendanceAllowanceType(models.Model):
    _name = "hr.attendance.allowance.type"
    _description = "Attendance Allowance Type"

    name = fields.Char(
        required=True,
        translate=True,
        help="Human-readable label for this allowance type, "
        "e.g. 'Travel Time', 'Dressing Time', 'Paid Break'.",
    )
    code = fields.Char(
        required=True,
        help="Technical identifier used to reference this allowance type"
        " in rules or reports. Must be unique per company.",
    )
    active = fields.Boolean(
        default=True,
        help="If unchecked, this allowance type will be hidden and unavailable for "
        "new rules.",
    )
    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
        help="Company that owns this allowance type.",
    )

    _sql_constraints = [
        (
            "code_company_uniq",
            "unique(code, company_id)",
            "The code must be unique per company.",
        ),
    ]
