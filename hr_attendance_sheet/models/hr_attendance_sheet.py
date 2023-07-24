# Copyright 2020 Pavlov Media
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class HrAttendanceSheet(models.Model):
    _name = "hr.attendance.sheet"
    _description = "Attendance Sheet"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    active = fields.Boolean(string="Active", default=True)
    name = fields.Char(compute="_compute_name")
    employee_id = fields.Many2one("hr.employee", string="Employee", required=True)
    user_id = fields.Many2one(
        "res.users", related="employee_id.user_id", string="User", store=True
    )
    start_date = fields.Date(string="Date From", required=True, index=True)
    end_date = fields.Date(string="Date To", required=True, index=True)
    attendance_ids = fields.One2many(
        "hr.attendance", "attendance_sheet_id", string="Attendances"
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirm", "Waiting Review"),
            ("done", "Approved"),
            ("locked", "Locked"),
        ],
        default="draft",
        tracking=True,
        string="Status",
        required=True,
        readonly=True,
        index=True,
    )
    company_id = fields.Many2one(
        "res.company", string="Company", related="employee_id.company_id"
    )
    department_id = fields.Many2one(
        "hr.department", string="Department", related="employee_id.department_id"
    )
    manager_id = fields.Many2one(
        "hr.employee", string="Manager", related="employee_id.parent_id"
    )
    working_hours = fields.Many2one(
        "resource.calendar",
        string="Working Hours",
        related="employee_id.resource_calendar_id",
    )
    hours_to_work = fields.Float(
        related="employee_id.hours_to_work",
        string="Hours to Work",
        help="""Expected working hours based on company policy. This is used \
             on attendance sheets to calculate overtime values.""",
    )
    total_time = fields.Float(compute="_compute_total_time", store=True)
    overtime = fields.Float(compute="_compute_overtime", store=True)
    can_review = fields.Boolean(
        string="Can Review", compute="_compute_can_review", search="_search_can_review"
    )
    reviewer_id = fields.Many2one(
        "hr.employee", string="Reviewer", readonly=True, tracking=True
    )
    reviewed_on = fields.Datetime(string="Reviewed On", readonly=True)
    review_policy = fields.Selection(
        string="Review Policy", related="company_id.attendance_sheet_review_policy"
    )
    attendance_admin = fields.Many2one(
        "hr.employee",
        string="Attendance Admin",
        help="""In addition to the employees manager, this person can
        administer attendances for all employees in the department. This field
        is set on the department.""",
        related="department_id.attendance_admin",
    )
    attendance_sheet_config_id = fields.Many2one(
        comodel_name="hr.attendance.sheet.config",
        compute="_compute_attendance_sheet_config_id",
    )

    def _compute_attendance_sheet_config_id(self):
        for sheet in self:
            config = self.env["hr.attendance.sheet.config"].search(
                [
                    ("start_date", "<=", sheet.start_date),
                    "|",
                    ("end_date", ">=", sheet.end_date),
                    ("end_date", "=", False),
                    ("company_id", "=", sheet.company_id.id),
                ]
            )
            sheet.attendance_sheet_config_id = config if config else None

    def _valid_field_parameter(self, field, name):
        # I can't even
        return name == "tracking" or super()._valid_field_parameter(field, name)

    # Automation Methods
    def activity_update(self):
        """Activity processing that shows in chatter for approval activity."""
        to_clean = self.env["hr.attendance.sheet"]
        to_do = self.env["hr.attendance.sheet"]
        external_id = "hr_attendance_sheet.mail_act_attendance_sheet_approval"
        for sheet in self:
            if sheet.state == "draft":
                to_clean |= sheet
            elif sheet.state == "confirm" and (
                sheet.review_policy == "employee_manager"
                or sheet.review_policy == "hr_or_manager"
            ):
                if sheet.sudo().employee_id.parent_id.user_id.id:
                    sheet.activity_schedule(
                        external_id,
                        user_id=sheet.sudo().employee_id.parent_id.user_id.id,
                    )

            elif sheet.state == "done":
                to_do |= sheet
        if to_clean:
            to_clean.activity_unlink([external_id])
        if to_do:
            to_do.activity_feedback([external_id])

    # Scheduled Action Methods
    def _create_sheet_id(self):
        """Method used by the scheduling action to auto create sheets."""
        companies = self.env["res.company"].search(
            [("use_attendance_sheets", "=", True)]
        )
        sheets = self.env["hr.attendance.sheet"]
        for company in companies:
            employees = self.env["hr.employee"].search(
                [
                    ("use_attendance_sheets", "=", True),
                    ("company_id", "=", company.id),
                    ("active", "=", True),
                ]
            )
            last_sheet = sheets.search(
                [("company_id", "=", company.id)], limit=1, order="end_date DESC"
            )
            next_sheet_date = None
            if last_sheet:
                next_sheet_date = last_sheet.end_date + relativedelta(days=1)
                config = self.env["hr.attendance.sheet.config"].search(
                    [
                        ("start_date", "<=", next_sheet_date),
                        ("company_id", "=", company.id),
                    ]
                )
            else:
                config = self.env["hr.attendance.sheet.config"].search(
                    [
                        ("company_id", "=", company.id),
                    ],
                    limit=1,
                    order="end_date DESC",
                )
            if not config:
                continue
            if not next_sheet_date:
                next_sheet_date = config.start_date
            if next_sheet_date <= fields.Date.today():
                for employee in employees:
                    sheet = self.env["hr.attendance.sheet"].create(
                        {
                            "employee_id": employee.id,
                            "start_date": next_sheet_date,
                            "end_date": config.compute_end_date(next_sheet_date),
                        }
                    )
                    sheets += sheet
        return sheets

    # Compute Methods
    @api.depends("employee_id", "start_date", "end_date")
    def _compute_name(self):
        for sheet in self:
            sheet.name = False
            if sheet.employee_id and sheet.start_date and sheet.end_date:
                sheet.name = (
                    sheet.employee_id.name
                    + " ("
                    + str(
                        datetime.strptime(
                            str(sheet.start_date), DEFAULT_SERVER_DATE_FORMAT
                        ).strftime("%m/%d/%y")
                    )
                    + " - "
                    + str(
                        datetime.strptime(
                            str(sheet.end_date), DEFAULT_SERVER_DATE_FORMAT
                        ).strftime("%m/%d/%y")
                    )
                    + ")"
                )

    @api.depends("attendance_ids.duration")
    def _compute_total_time(self):
        for sheet in self:
            sheet.total_time = 0.0
            if sheet.attendance_ids:
                sheet.total_time = sum(sheet.mapped("attendance_ids.duration"))

    @api.depends("total_time")
    def _compute_overtime(self):
        for sheet in self:
            overtime = sheet.total_time - sheet.hours_to_work
            if overtime < 0.0:
                sheet.overtime = 0.0
            else:
                sheet.overtime = overtime

    @api.depends("review_policy")
    def _compute_can_review(self):
        self.can_review = False
        for sheet in self:
            if self.env.user in sheet._get_possible_reviewers():
                sheet.can_review = True

    # Reviewer Methods
    def _get_possible_reviewers(self):
        res = self.env["res.users"].browse(SUPERUSER_ID)
        if self.review_policy == "hr":
            res |= self.env.ref("hr.group_hr_user").users
        elif self.review_policy == "employee_manager":
            if (
                self.department_id.attendance_admin
                and self.department_id.attendance_admin != self.employee_id
            ):
                res |= (
                    self.employee_id.parent_id.user_id
                    + self.department_id.attendance_admin.user_id
                )
            else:
                res |= self.employee_id.parent_id.user_id
        elif self.review_policy == "hr_or_manager":
            if (
                self.department_id.attendance_admin
                and self.department_id.attendance_admin != self.employee_id
            ):
                res |= (
                    self.employee_id.parent_id.user_id
                    + self.env.ref("hr.group_hr_user").users
                    + self.department_id.attendance_admin.user_id
                )
            else:
                res |= (
                    self.employee_id.parent_id.user_id
                    + self.env.ref("hr.group_hr_user").users
                )
        return res

    def _check_can_review(self):
        if self.filtered(lambda x: not x.can_review and x.review_policy == "hr"):
            raise UserError(_("""Only a HR Officer can review the sheet."""))
        elif self.filtered(
            lambda x: not x.can_review and x.review_policy == "employee_manager"
        ):
            raise UserError(
                _(
                    """Only the Manager of the Employee can review
            the sheet."""
                )
            )
        elif self.filtered(
            lambda x: not x.can_review and x.review_policy == "hr_or_manager"
        ):
            raise UserError(
                _(
                    """Only the Manager of the Employee or an HR
            Officer/Manager can review the sheet."""
                )
            )
        else:
            return True

    # Create/Write Methods
    @api.model
    def create(self, vals):
        """On create, link existing attendances."""
        res = super(HrAttendanceSheet, self).create(vals)
        attendances = self.env["hr.attendance"].search(
            [
                ("employee_id", "=", res.employee_id.id),
                ("attendance_sheet_id", "=", False),
                ("check_in", ">=", res.start_date),
                ("check_in", "<=", res.end_date),
                "|",
                ("check_out", "=", False),
                "&",
                ("check_out", ">=", res.start_date),
                ("check_out", "<=", res.end_date),
            ]
        )
        attendances._compute_attendance_sheet_id()
        return res

    def write(self, values):
        """Prevent writing on a locked sheet."""
        protected_fields = [
            "employee_id",
            "name",
            "attendance_ids",
            "start_date",
            "end_date",
        ]
        for record in self:
            if record.state == "locked" and any(
                f in values.keys() for f in protected_fields
            ):
                raise UserError(_("You can't edit a locked sheet."))
            elif (
                record.state in ("confirm", "done")
                and self.env.user not in record._get_possible_reviewers()
            ):
                raise UserError(
                    _("You don't have permission to edit submitted/approved sheets")
                )
        return super(HrAttendanceSheet, self).write(values)

    # BUTTON ACTIONS
    def attendance_action_change(self):
        """Call to perform Check In/Check Out action"""
        return self.employee_id._attendance_action_change()

    def action_attendance_sheet_confirm(self):
        """Restrict to submit sheet contains attendance without checkout."""
        for sheet in self:
            ids_not_checkout = sheet.attendance_ids.filtered(
                lambda att: att.check_in and not att.check_out
            )
            if not ids_not_checkout:
                sheet.write({"state": "confirm"})
                sheet.activity_update()
            else:
                raise UserError(
                    _(
                        "The sheet cannot be validated as it does not "
                        + "contain an equal number of check-ins and check-outs."
                    )
                )

    def action_attendance_sheet_draft(self):
        """Convert to Draft button."""
        if self.filtered(lambda sheet: sheet.state != "done"):
            raise UserError(_("Cannot revert to draft a non-approved sheet."))
        self._check_can_review()
        self.write({"state": "draft", "reviewer_id": False, "reviewed_on": False})
        self.activity_update()
        return True

    def action_attendance_sheet_done(self):
        """Approve button."""
        if self.filtered(lambda sheet: sheet.state != "confirm"):
            raise UserError(_("Cannot approve a non-submitted sheet."))
        reviewer = self.env.user.employee_id
        if not reviewer:
            raise UserError(
                _(
                    """In order to review a attendance sheet,
            your user needs to be linked to an employee record."""
                )
            )
        self._check_can_review()
        self.write(
            {
                "state": "done",
                "reviewer_id": reviewer.id,
                "reviewed_on": fields.Datetime.now(),
            }
        )
        self.activity_update()
        return True

    def action_attendance_sheet_lock(self):
        """Lock button to lock the sheet and prevent any changes."""
        if self.filtered(lambda sheet: sheet.state != "done"):
            raise UserError(_("Cannot lock a non-approved sheet."))
        elif not self.env.user.has_group("hr_attendance.group_hr_attendance_user"):
            raise UserError(_("You do not have permissions to lock sheets."))
        else:
            self.write({"state": "locked"})
        return True

    def action_attendance_sheet_unlock(self):
        """Unlock button, moves back to Confirm (Must have HR Group)."""
        if not self.env.user.has_group("hr_attendance.group_hr_attendance_user"):
            raise UserError(_("You do not have permissions to unlock sheets."))
        else:
            self.write({"state": "done"})
        return True

    def action_attendance_sheet_refuse(self):
        """Refuse button sending back to draft."""
        if self.filtered(lambda sheet: sheet.state != "confirm"):
            raise UserError(_("Cannot reject a non-submitted sheet."))
        self._check_can_review()
        self.write({"state": "draft", "reviewer_id": False, "reviewed_on": False})
        self.activity_update()
        return True
