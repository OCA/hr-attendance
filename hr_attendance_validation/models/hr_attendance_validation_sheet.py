# Copyright 2021 Pierre Verkest
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from datetime import timedelta

from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.osv import expression


class HrAttendanceValidationSheet(models.Model):
    _name = "hr.attendance.validation.sheet"
    _description = "Attendance validation sheet that helps managers review attendances."
    _order = "date_from desc, employee_id asc"

    def _default_from_date(self):
        """returns the monday before last sunday"""
        today = fields.Date.today()
        return today - timedelta(days=today.weekday() + 7)

    def _default_to_date(self):
        """returns last sunday"""
        today = fields.Date.today()
        return today - timedelta(days=today.weekday() + 1)

    def name_get(self):
        results = []
        for rec in self:
            results.append(
                (
                    rec.id,
                    _("Week %s - %s")
                    % (
                        rec.date_from.strftime("%W"),
                        rec.employee_id.name,
                    ),
                )
            )
        return results

    state = fields.Selection(
        [
            ("draft", "To review"),
            ("validated", "Validated"),
        ],
        string="State",
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
        related="calendar_id.total_hours",
        help="Theoretical calendar hours to spend by week.",
    )
    attendance_ids = fields.One2many(
        "hr.attendance", inverse_name="validation_sheet_id", string="Attendances"
    )
    attendance_due_ids = fields.One2many(
        "hr.attendance",
        compute="_compute_attendance_due_ids",
        string="Valid attendances",
    )
    leave_ids = fields.Many2many("hr.leave", string="Leaves")
    leave_allocation_id = fields.Many2one(
        "hr.leave.allocation",
        string="Leave allocation",
        help="Automatically generated on validation if compensatory_hour > 0",
    )
    leave_id = fields.Many2one(
        "hr.leave",
        string="Leave",
        help="Automatically generated on validation if "
        "regularization_compensatory_hour_taken > 0",
    )

    leave_hours = fields.Float(
        "Leaves (hours)",
        compute="_compute_leaves",
        help="Compute number of leaves in hours",
    )
    attendance_hours = fields.Float(
        "Attendance (hours)",
        compute="_compute_attendances_hours",
        help="Compute number of attendance lines not marked as overtime",
    )
    attendance_total_hours = fields.Float(
        "Total Attendance (hours)",
        compute="_compute_attendances_hours",
        help="Validated attendances. Sum attendance and due overtime lines.",
    )
    overtime_due_hours = fields.Float(
        "Overtime due (hours)",
        compute="_compute_attendances_hours",
        help="Compute number of attendance lines marked as overtime which are marked as due",
    )
    overtime_not_due_hours = fields.Float(
        "Overtime not due (hours)",
        compute="_compute_attendances_hours",
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

    @api.onchange("employee_id", "date_from", "date_to")
    def _onchange_recompute_lines(self):
        self.ensure_one()
        self.require_regeneration = True

    @api.depends("leave_ids")
    def _compute_leaves(self):
        for record in self:
            leave_hours = 0
            for leave in record.leave_ids:
                if leave.request_unit_half or leave.request_unit_hours:
                    # we assume time off is recorded by hours
                    leave_hours += leave.number_of_hours_display
                else:
                    # As far leaves can be record on multiple weeks
                    # intersect calendar attendance and leaves date
                    # to compute theoretical leave time
                    current_date = max(leave.request_date_from, record.date_from)
                    date_to = min(
                        leave.request_date_to or leave.request_date_from, record.date_to
                    )
                    while current_date <= date_to:
                        leave_hours += sum(
                            record.calendar_id.attendance_ids.filtered(
                                lambda att: int(att.dayofweek) == current_date.weekday()
                            ).mapped(lambda att: att.hour_to - att.hour_from)
                        )
                        current_date += timedelta(days=1)

            record.leave_hours = leave_hours

    @api.depends("attendance_ids", "attendance_ids.is_overtime")
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
                record.attendance_due_ids.mapped("worked_hours")
            )

    def _compute_attendance_due_ids(self):
        for record in self:
            record.attendance_due_ids = record.attendance_ids.filtered(
                lambda att: not att.is_overtime or att.is_overtime_due
            )

    def _retrieve_attendance(self):
        """Method that link to hr.attendance between date from and date to"""
        HrAttendance = self.env["hr.attendance"]
        for record in self:
            record.attendance_ids = HrAttendance.search(
                [
                    ("employee_id", "=", record.employee_id.id),
                    ("check_in", ">=", record.date_from),
                    ("check_in", "<=", record.date_to),
                ],
            )

    def _retrieve_leave(self):
        """Method that link to hr.leave between date from and date to"""
        HrLeave = self.env["hr.leave"]
        for record in self:
            domain = expression.AND(
                [
                    [
                        ("state", "in", ["validate", "validate1"]),
                        ("employee_id", "=", record.employee_id.id),
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
                            # leaves thats start before and ends after the validation sheet
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
            record.leave_ids = HrLeave.search(domain)

    def action_retrieve_attendance_and_leaves(self):
        """Action to retrieve both attendance and leave lines"""
        self._retrieve_attendance()
        self._retrieve_leave()
        # this method can be called by cron, ensure that properly recompute
        # default comp hours
        self._compute_default_compensatory_hour()
        self.require_regeneration = False

    def action_validate(self):
        """Method to validate this sheet and generate leave allocation
        if necessary
        """
        HrLeave = self.env["hr.leave"]
        HrAllocation = self.env["hr.leave.allocation"]
        holiday_status_id = int(
            self.env["ir.config_parameter"]
            .with_user(SUPERUSER_ID)
            ._get_param("hr_attendance_validation.leave_type_id")
            or self.env.ref("hr_holidays.holiday_status_comp").id
        )

        for record in self:
            if record.compensatory_hour > 0 and not record.leave_allocation_id:
                record.leave_allocation_id = HrAllocation.create(
                    {
                        "employee_id": record.employee_id.id,
                        "holiday_status_id": holiday_status_id,
                        "number_of_days": record.compensatory_hour
                        / record.calendar_id.hours_per_day,
                        "holiday_type": "employee",
                        "state": "validate",
                        "name": _("Compensatory hours: %s") % record.display_name,
                        "notes": _(
                            "Allocation created and validated from attendance "
                            "validation reviews: %s"
                        )
                        % record.display_name,
                    }
                )

            if (
                record.regularization_compensatory_hour_taken > 0
                and not record.leave_id
            ):
                record.leave_id = HrLeave.create(
                    {
                        "employee_id": record.employee_id.id,
                        "holiday_status_id": holiday_status_id,
                        "number_of_days": record.regularization_compensatory_hour_taken
                        / record.calendar_id.hours_per_day,
                        "name": _("Compensatory hours regularization generated from %s")
                        % record.display_name,
                        "request_date_from": record.date_to,
                        "request_date_to": record.date_to,
                        "date_from": record.date_to,
                        "date_to": record.date_to,
                        "request_unit_hours": False,
                    }
                )
                record.leave_id.action_validate()
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
        for employee in self.env["hr.employee"].search([("active", "=", True)]):
            reviews += self.create(
                {
                    "employee_id": employee.id,
                }
            )
        reviews.action_retrieve_attendance_and_leaves()
        return reviews

    def action_to_review(self):
        self.write({"state": "draft"})
