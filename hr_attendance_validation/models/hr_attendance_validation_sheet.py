# Copyright 2021 Pierre Verkest
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from datetime import datetime, timedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.osv import expression


class HrAttendanceValidationSheet(models.Model):
    _name = "hr.attendance.validation.sheet"
    _description = "Attendance validation sheet that helps managers review attendances."
    _order = "date_from desc, employee_id asc"

    def _default_from_date(self):
        """returns the monday before last sunday"""
        today = fields.Date.today()
        return fields.Date.subtract(today, days=today.weekday() + 7)

    def _default_to_date(self):
        """returns last sunday"""
        today = fields.Date.today()
        return fields.Date.subtract(today, days=today.weekday() + 1)

    @api.depends("employee_id.name", "date_from")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = _("Week %(week_name)s - %(employee_name)s") % dict(
                week_name=rec.date_from.strftime("%W"),
                employee_name=rec.employee_id.name,
            )

    state = fields.Selection(
        [
            ("draft", "To review"),
            ("validated", "Validated"),
        ],
        required=True,
        default="draft",
    )
    date_from = fields.Date(
        string="Date from",
        required=True,
        default=_default_from_date,
    )
    date_to = fields.Date(
        string="Date to",
        required=True,
        default=_default_to_date,
    )
    employee_id = fields.Many2one(
        "hr.employee",
        string="Employee",
        required=True,
        ondelete="cascade",
        index=True,
    )
    calendar_id = fields.Many2one(
        "resource.calendar",
        string="Calendar",
        related="employee_id.resource_calendar_id",
    )
    theoretical_hours = fields.Float(
        string="Theoretical (hours)",
        compute="_compute_theoretical_hours",
        store=True,
        help="theoretical calendar hours to spend by week.",
    )
    attendance_ids = fields.One2many(
        "hr.attendance", inverse_name="validation_sheet_id", string="Attendances"
    )
    attendance_due_ids = fields.One2many(
        "hr.attendance",
        compute="_compute_attendance_due_ids",
        string="Used to display attendances in the view.",
    )
    leave_ids = fields.Many2many("hr.leave", string="Leaves")
    overtime_ids = fields.Many2many(
        "hr.attendance.overtime",
        domain=[("adjustment", "=", True), ("duration", "<", 0)],
        help="Compensatory hours taken",
    )
    adjustment_overtime_id = fields.Many2one(
        "hr.attendance.overtime",
    )

    leave_hours = fields.Float(
        "Leaves (hours)",
        compute="_compute_leaves",
        store=True,
        help="Compute number of leaves in hours",
    )
    compensatory_leave_hours = fields.Float(
        "Compensatory Leaves (hours)",
        compute="_compute_leaves",
        store=True,
        help="Compute number of compensatory leaves taken (in hours)",
    )

    attendance_hours = fields.Float(
        "Attendance (hours)",
        compute="_compute_attendances_hours",
        store=True,
        help="Compute number of attendance lines not marked as overtime",
    )
    attendance_total_hours = fields.Float(
        "Total Attendance (hours)",
        compute="_compute_attendances_hours",
        store=True,
        help="Validated attendances. Sum attendance and due overtime lines.",
    )
    overtime_due_hours = fields.Float(
        "Overtime due (hours)",
        compute="_compute_attendances_hours",
        store=True,
        help=(
            "Compute number of attendance lines marked as "
            "overtime which are marked as due"
        ),
    )
    overtime_not_due_hours = fields.Float(
        "Overtime not due (hours)",
        compute="_compute_attendances_hours",
        store=True,
        help="Compute number of attendance lines marked as overtime which are not due",
    )
    compensatory_hour = fields.Float(
        "Compensatory hour",
        help="Compensatory hours that will be allocated to the employee.",
    )
    regularization_compensatory_hour_taken = fields.Float(
        "Regularization compensatory hours' taken",
        help="Compensatory hours that will be counted as leaves for the employee.",
    )
    require_regeneration = fields.Boolean(
        "Require regeneration",
        default=False,
        help="Couldn't properly call action retrieve lines in onchange "
        "instead alert user to click on it when needs.",
    )

    @api.onchange(
        "employee_id",
        "date_from",
        "date_to",
        "employee_id.weekly_attendance_validation",
    )
    def _onchange_recompute_lines(self):
        self.ensure_one()
        self.require_regeneration = True

    @api.depends("calendar_id", "date_from", "date_to")
    def _compute_theoretical_hours(self):
        for record in self:
            if record.calendar_id.exists():
                record.theoretical_hours = record.with_context(
                    employee_id=record.employee_id.id, exclude_public_holidays=True
                ).calendar_id.get_work_hours_count(
                    datetime.combine(record.date_from, datetime.min.time()),
                    datetime.combine(record.date_to, datetime.max.time()),
                    compute_leaves=False,
                )
            else:
                record.theoretical_hours = 0

    def _compute_leaves_hours(self):
        self.ensure_one()

        leave_hours = 0
        for leave in self.leave_ids:
            if leave.request_unit_half or leave.request_unit_hours:
                # we assume time off is recorded by hours
                leave_hours += leave.number_of_hours_display
            else:
                # As far leaves can be record on multiple weeks
                # intersect calendar attendance and leaves date
                # to compute theoretical leave time
                current_date = max(leave.request_date_from, self.date_from)
                date_to = min(
                    leave.request_date_to or leave.request_date_from, self.date_to
                )
                while current_date <= date_to:
                    current_date_leave_hours = sum(
                        self.calendar_id.attendance_ids.filtered(
                            lambda att, current_date=current_date: att.day_period
                            != "lunch"
                            and int(att.dayofweek) == current_date.weekday()
                        ).mapped(lambda att: att.hour_to - att.hour_from)
                    )
                    leave_hours += current_date_leave_hours
                    current_date += timedelta(days=1)
        return leave_hours

    @api.depends("leave_ids")
    def _compute_leaves(self):
        for record in self:
            leave_hours = record._compute_leaves_hours()
            record.compensatory_leave_hours = abs(
                sum(record.overtime_ids.mapped("duration"))
            )
            record.leave_hours = leave_hours + record.compensatory_leave_hours

    @api.depends(
        "attendance_ids",
        "attendance_ids.is_overtime",
        "attendance_ids.is_overtime_due",
    )
    def _compute_attendances_hours(self):
        for record in self:
            record.attendance_hours = sum(
                record.attendance_ids.filtered(lambda att: not att.is_overtime).mapped(
                    "worked_hours"
                )
            )
            record.overtime_due_hours = sum(
                record.attendance_ids.filtered(
                    lambda att: att.is_overtime and att.is_overtime_due
                ).mapped("worked_hours")
            )
            record.overtime_not_due_hours = sum(
                record.attendance_ids.filtered(
                    lambda att: att.is_overtime and not att.is_overtime_due
                ).mapped("worked_hours")
            )
            record.attendance_total_hours = sum(
                record.attendance_ids.filtered(
                    lambda att: not att.is_overtime or att.is_overtime_due
                ).mapped("worked_hours")
            )

    @api.depends(
        "attendance_ids", "attendance_ids.is_overtime", "attendance_ids.is_overtime_due"
    )
    def _compute_attendance_due_ids(self):
        see_all_attendance = self.env.user.has_group(
            "hr_attendance.group_hr_attendance_manager"
        )
        for record in self:
            record.attendance_due_ids = record.attendance_ids.filtered(
                lambda att: see_all_attendance
                or not att.is_overtime
                or att.is_overtime_due
            )

    def _retrieve_attendance(self):
        """Method that link to hr.attendance between date from and date to"""
        for record in self:
            if not record.employee_id.weekly_attendance_validation:
                record.attendance_ids = self.env["hr.attendance"].browse()
                continue
            record.attendance_ids = self.env["hr.attendance"].search(
                [
                    ("employee_id", "=", record.employee_id.id),
                    ("check_in", ">=", record.date_from),
                    ("check_in", "<=", record.date_to),
                ],
            )

    def _retrieve_overtime(self):
        for record in self:
            if not record.employee_id.weekly_attendance_validation:
                record.overtime_ids = self.env["hr.attendance.overtime"].browse()
                continue
            record.overtime_ids = self.env["hr.attendance.overtime"].search(
                [
                    ("employee_id", "=", record.employee_id.id),
                    ("date", ">=", record.date_from),
                    ("date", "<=", record.date_to),
                    ("adjustment", "=", True),
                    ("duration", "<", 0),
                ],
            )

    def _retrieve_leave(self):
        """Method that link to hr.leave between date from and date to"""
        for record in self:
            if not record.employee_id.weekly_attendance_validation:
                record.leave_ids = self.env["hr.leave"].browse()
                continue
            domain = expression.AND(
                [
                    [
                        ("state", "in", ["validate", "validate1"]),
                        ("employee_id", "=", record.employee_id.id),
                        (
                            "holiday_status_id.time_type",
                            "=",
                            "leave",
                        ),
                        # those leave/allocations use hr.attendance.overtime as
                        # backend to store data
                        ("holiday_status_id.overtime_deductible", "=", False),
                    ],
                    expression.OR(
                        [
                            # leaves thats starts in the validation sheet interval
                            expression.AND(
                                [
                                    [("request_date_from", ">=", record.date_from)],
                                    [("request_date_from", "<=", record.date_to)],
                                ]
                            ),
                            # leaves thats ends in the validation sheet interval
                            expression.AND(
                                [
                                    [("request_date_to", ">=", record.date_from)],
                                    [("request_date_to", "<=", record.date_to)],
                                ]
                            ),
                            # leaves thats start before and ends after
                            # the validation sheet
                            expression.AND(
                                [
                                    [("request_date_from", "<", record.date_from)],
                                    [("request_date_to", ">", record.date_to)],
                                ]
                            ),
                        ]
                    ),
                ]
            )
            record.leave_ids = self.env["hr.leave"].search(domain)

    def action_retrieve_attendance_and_leaves(self):
        """Action to retrieve both attendance and leave lines"""
        self._retrieve_attendance()
        self._retrieve_leave()
        self._retrieve_overtime()
        # this method can be called by cron, ensure that properly recompute
        # default comp hours
        self._compute_default_compensatory_hour()
        self.require_regeneration = False

    def action_validate(self):
        """Method to validate this sheet and generate leave allocation
        if necessary
        """
        for record in self:
            if not record.employee_id.weekly_attendance_validation:
                raise ValidationError(
                    _(
                        "Can't validate weekly validation attendance sheets "
                        "for %(employee_name)s. Please first choose 'Weekly "
                        "compensatory computation' on employee form."
                    )
                    % dict(
                        employee_name=record.employee_id.name,
                    )
                )
            duration = 0
            if record.compensatory_hour > 0:
                duration = record.compensatory_hour

            if record.regularization_compensatory_hour_taken > 0:
                duration = -record.regularization_compensatory_hour_taken

            if duration:
                record.adjustment_overtime_id = self.env[
                    "hr.attendance.overtime"
                ].create(
                    {
                        "employee_id": record.employee_id.id,
                        "date": record.date_to,
                        "duration": duration,
                        "duration_real": duration,
                        "adjustment": True,
                    }
                )
                record.action_retrieve_attendance_and_leaves()
            record.state = "validated"

    @api.onchange(
        "leave_hours",
        "attendance_hours",
        "overtime_due_hours",
        "overtime_not_due_hours",
    )
    def _compute_default_compensatory_hour(self):
        """Re-compute default compensatory hour based on
        accepted overtime
        """
        for record in self:
            diff = (
                record.attendance_hours
                + record.leave_hours
                + record.overtime_due_hours
                - record.theoretical_hours
            )
            record.compensatory_hour = max(0, diff)
            record.regularization_compensatory_hour_taken = abs(min(0, diff))

    @api.model
    def generate_reviews(self):
        reviews = self.env["hr.attendance.validation.sheet"]
        for employee in self.env["hr.employee"].search(
            [
                ("weekly_attendance_validation", "=", True),
            ]
        ):
            reviews += self.create(
                {
                    "employee_id": employee.id,
                }
            )
        reviews.action_retrieve_attendance_and_leaves()
        return reviews

    def action_to_review(self):
        self.adjustment_overtime_id.unlink()
        self.write({"state": "draft"})
        self.action_retrieve_attendance_and_leaves()
