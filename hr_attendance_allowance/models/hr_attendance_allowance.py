# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class HrAttendanceAllowance(models.Model):
    _name = "hr.attendance.allowance"
    _description = "Attendance Allowance"
    _check_company_auto = True

    attendance_id = fields.Many2one(
        "hr.attendance",
        required=True,
        ondelete="cascade",
        index=True,
        help="Attendance record this allowance line belongs to.",
    )
    type_id = fields.Many2one(
        "hr.attendance.allowance.type",
        required=True,
        help="Category of allowance granted, "
        "e.g. travel time, dressing time, paid break.",
        check_company=True,
    )
    minutes = fields.Integer(
        required=True,
        help="Duration of the allowance expressed in minutes.",
    )
    origin = fields.Selection(
        [("automatic", "Automatic"), ("manual", "Manual")],
        required=True,
        default="automatic",
        help="Indicates whether this allowance was computed automatically by the rule "
        "engine or added manually by a user.",
    )
    note = fields.Char(
        translate=True,
        help="Optional description or justification for this allowance line.",
    )
    employee_id = fields.Many2one(
        "hr.employee",
        related="attendance_id.employee_id",
        store=True,
        readonly=True,
        index=True,
        help="Employee derived from the linked attendance record.",
    )
    check_in = fields.Datetime(
        related="attendance_id.check_in",
        store=True,
        readonly=True,
        index=True,
        help="Check-in time derived from the linked attendance record.",
    )
    company_id = fields.Many2one(
        "res.company",
        related="attendance_id.employee_id.company_id",
        store=True,
        readonly=True,
        help="Company derived from the employee linked to the attendance record.",
    )
