# Copyright 2021 Pierre Verkest
# Copyright 2023 ACSONE SA/NV
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.osv import expression


class HrAttendanceSheet(models.Model):
    _inherit = "hr.attendance.sheet"

    theoretical_hours = fields.Float(
        string="Theoretical (hours)",
        related="working_hours.total_hours",
        help="Theoretical calendar hours to spend by week.",
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
    attendance_full_hours = fields.Float(
        "Attendance (Full hours)",
        compute="_compute_attendances_hours",
        help="Compute number of attendance lines",
    )
    attendance_hours = fields.Float(
        "Attendance without overtime",
        compute="_compute_attendances_hours",
        help="Compute number of attendance lines not marked as overtime",
    )
    attendance_total_hours = fields.Float(
        "Total Attendance (without lunch - Not Due)",
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
    start_date = fields.Date(
        default=lambda self: self._default_start_date(),
    )
    end_date = fields.Date(
        default=lambda self: self._default_end_date(),
    )

    def _default_start_date(self):
        """returns the monday before last sunday"""
        today = fields.Date.today()
        return today - timedelta(days=today.weekday() + 7)

    def _default_end_date(self):
        """returns last sunday"""
        today = fields.Date.today()
        return today - timedelta(days=today.weekday() + 1)

    @api.depends("leave_ids")
    def _compute_leaves(self):
        for record in self:
            leave_hours = 0
            for leave in record.leave_ids:
                if leave.request_unit_half or leave.request_unit_hours:
                    # we assume time off is recorded by hours
                    leave_hours += leave.sudo().number_of_hours_display
                else:
                    # As far leaves can be record on multiple weeks
                    # intersect calendar attendance and leaves date
                    # to compute theoretical leave time
                    current_date = max(leave.request_date_from, record.start_date)
                    date_to = min(
                        leave.request_date_to or leave.request_date_from,
                        record.end_date,
                    )
                    while current_date <= date_to:
                        leave_hours += sum(
                            record.working_hours.attendance_ids.filtered(
                                lambda att: int(att.dayofweek) == current_date.weekday()
                            ).mapped(lambda att: att.hour_to - att.hour_from)
                        )
                        current_date += timedelta(days=1)

            record.leave_hours = leave_hours

    @api.depends("attendance_ids", "attendance_ids.is_overtime")
    def _compute_attendances_hours(self):
        for record in self:
            record.attendance_full_hours = sum(
                record.attendance_ids.mapped("worked_hours")
            )
            record.attendance_hours = sum(
                record.attendance_ids.filtered(lambda att: not att.is_overtime).mapped(
                    "duration"
                )
            )
            record.overtime_due_hours = sum(
                record.attendance_ids.filtered(
                    lambda att: att.is_overtime and att.is_overtime_due
                ).mapped("duration")
            )
            record.overtime_not_due_hours = sum(
                record.attendance_ids.filtered(
                    lambda att: att.is_overtime and not att.is_overtime_due
                ).mapped("duration")
            )
            record.attendance_total_hours = sum(
                record.attendance_due_ids.mapped("duration")
            )

    def _compute_attendance_due_ids(self):
        for record in self:
            record.attendance_due_ids = record.attendance_ids.filtered(
                lambda att: not att.is_overtime or att.is_overtime_due
            )

    @api.onchange("employee_id", "start_date", "end_date")
    def _onchange_recompute_lines(self):
        self.ensure_one()
        self.require_regeneration = True

    def _retrieve_attendance(self):
        """Method that link to hr.attendance between date from and date to"""
        HrAttendance = self.env["hr.attendance"]
        for record in self:
            record.attendance_ids = HrAttendance.search(
                [
                    ("employee_id", "=", record.employee_id.id),
                    ("check_in", ">=", record.start_date),
                    ("check_in", "<=", record.end_date),
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
                                    [("request_date_from", ">=", record.start_date)],
                                    [("request_date_from", "<=", record.end_date)],
                                ]
                            ),
                            # leaves thats ends in the validation sheet interval
                            expression.AND(
                                [
                                    [("request_date_to", ">=", record.start_date)],
                                    [("request_date_to", "<=", record.end_date)],
                                ]
                            ),
                            # leaves thats start before and ends after the validation sheet
                            expression.AND(
                                [
                                    [("request_date_from", "<", record.start_date)],
                                    [("request_date_to", ">", record.end_date)],
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

    def action_attendance_sheet_done(self):
        """Method to validate this sheet and generate leave allocation
        if necessary
        """
        self.generate_leave_allocation()
        self.generate_leave()
        res = super().action_attendance_sheet_done()
        return res

    def action_attendance_sheet_draft(self):
        self.clear_leaves_and_allocation()
        return super().action_attendance_sheet_draft()

    def clear_leaves_and_allocation(self):
        for record in self:
            if record.leave_allocation_id:
                record.leave_allocation_id.action_refuse()
                record.leave_allocation_id.action_draft()
            if record.leave_id:
                record.leave_id.action_refuse()
                record.leave_id.action_draft()
        self.remove_leaves()

    def remove_leaves(self):
        for record in self:
            record.leave_allocation_id = False
            record.leave_id = False

    def unlink(self):
        self.clear_leaves_and_allocation()
        return super().unlink()

    def generate_leave_allocation(self):
        HrAllocation = self.env["hr.leave.allocation"]
        for sheet in self:
            holiday_status_id = sheet.config_holiday_status_leave_allocation().id
            if sheet.compensatory_hour > 0 and not sheet.leave_allocation_id:
                sheet.leave_allocation_id = HrAllocation.create(
                    {
                        "employee_id": sheet.employee_id.id,
                        "holiday_status_id": holiday_status_id,
                        "number_of_days": sheet.compensatory_hour
                        / sheet.working_hours.hours_per_day,
                        "holiday_type": "employee",
                        "state": "validate",
                        "private_name": _("Compensatory hours: %s")
                        % sheet.display_name,
                        "notes": _(
                            "Allocation created and validated from attendance "
                            "validation reviews: %s"
                        )
                        % sheet.display_name,
                    }
                )
        return HrAllocation

    def config_holiday_status_leave_allocation(self):
        self.ensure_one()
        return self.employee_id.company_id.hr_attendance_compensatory_leave_type_id

    def generate_leave(self):
        HrLeave = self.env["hr.leave"]
        for sheet in self:
            holiday_status_id = sheet.config_holiday_status_leave().id
            if sheet.regularization_compensatory_hour_taken > 0 and not sheet.leave_id:
                leave = HrLeave.create(
                    {
                        "employee_id": sheet.employee_id.id,
                        "holiday_status_id": holiday_status_id,
                        "number_of_days": sheet.regularization_compensatory_hour_taken
                        / sheet.working_hours.hours_per_day,
                        "name": _("Compensatory hours regularization generated from %s")
                        % sheet.display_name,
                        "request_date_from": sheet.end_date,
                        "request_date_to": sheet.end_date,
                        "date_from": sheet.end_date,
                        "date_to": sheet.end_date,
                        "request_unit_hours": False,
                    }
                )
                leave.action_validate()
                sheet.leave_id = leave
        return HrLeave

    def config_holiday_status_leave(self):
        self.ensure_one()
        return self.employee_id.company_id.hr_attendance_compensatory_leave_type_id

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
                - record.hours_to_work
            )
            record.compensatory_hour = max(0, diff)
            record.regularization_compensatory_hour_taken = abs(min(0, diff))

    @api.model
    def _create_sheet_id(self):
        sheets = super()._create_sheet_id()
        sheets.action_retrieve_attendance_and_leaves()
        return sheets

    def action_to_review(self):
        self.write({"state": "draft"})

    def action_compute_compensatory_hour(self):
        self._compute_default_compensatory_hour()
