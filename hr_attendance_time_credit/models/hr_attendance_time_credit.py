# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class HrAttendanceTimeCredit(models.Model):
    _name = "hr.attendance.time.credit"
    _description = "Attendance Time Credit"
    _check_company_auto = True

    attendance_id = fields.Many2one(
        "hr.attendance",
        required=True,
        ondelete="cascade",
        index=True,
        help="Attendance record this credit line belongs to.",
    )
    type_id = fields.Many2one(
        "hr.attendance.time.credit.type",
        required=True,
        help="Category of time credit granted, "
        "e.g. travel time, dressing time, paid break, sunday premium.",
        check_company=True,
    )
    rule_id = fields.Many2one(
        "hr.attendance.time.credit.rule",
        ondelete="set null",
        readonly=True,
        index=True,
        help="Rule that generated this credit line. "
        "Empty for manually created credits.",
    )
    minutes = fields.Integer(
        required=True,
        help="Duration of the time credit expressed in minutes.",
    )
    origin = fields.Selection(
        [("automatic", "Automatic"), ("manual", "Manual")],
        required=True,
        default="manual",
        help="Indicates whether this credit was computed automatically by the rule "
        "engine or added manually by a user. Lines added by hand default to "
        "Manual so the engine leaves them alone; it only ever removes and "
        "recreates the lines it created itself (origin Automatic).",
    )
    note = fields.Char(
        translate=True,
        help="Optional description or justification for this credit line.",
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
    segment_date = fields.Date(
        help="Calendar date this credit line applies to. Set when the parent "
        "attendance spans multiple days and the rule uses per-day evaluation.",
    )
    segment_hours = fields.Float(
        help="Hours in this specific day segment. Set alongside segment_date.",
    )

    @api.model
    def _check_locked_attendances(self, attendance_ids):
        """Refuse edits to credit lines of a credit-locked attendance.

        sudo: the lock is a property of the attendance, not a permission of the
        editor, so an attendance officer editing a line is stopped by it too.
        """
        locked = (
            self.env["hr.attendance"]
            .sudo()
            .browse([id_ for id_ in attendance_ids if id_])
            .filtered("credit_locked")
        )
        if locked:
            raise UserError(
                _(
                    "This attendance is locked (Credit Locked). Unlock it before "
                    "adding, changing or removing its time credits."
                )
            )

    @api.model_create_multi
    def create(self, vals_list):
        self._check_locked_attendances(
            [vals["attendance_id"] for vals in vals_list if vals.get("attendance_id")]
        )
        return super().create(vals_list)

    def write(self, vals):
        self._check_locked_attendances(self.attendance_id.ids)
        if vals.get("attendance_id"):
            self._check_locked_attendances([vals["attendance_id"]])
        return super().write(vals)

    def unlink(self):
        # Deleting the attendance itself cascades at the database level and never
        # reaches this method, so a locked record only blocks direct unlinks.
        self._check_locked_attendances(self.attendance_id.ids)
        return super().unlink()
