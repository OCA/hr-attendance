# Copyright 2023 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)


from datetime import datetime, timedelta

from odoo import _, api, fields, models
from odoo.osv.expression import AND, OR


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    break_ids = fields.One2many("hr.attendance.break", "attendance_id", string="Breaks")
    break_hours = fields.Float(store=True, compute="_compute_break_hours")

    @api.constrains("check_in", "check_out")
    def _check_times_break(self):
        self.mapped("break_ids")._check_times()

    @api.depends("break_ids.begin", "break_ids.end")
    def _compute_break_hours(self):
        """Compute break hours"""
        for this in self:
            this.break_hours = sum(
                this.break_ids.filtered(
                    lambda x: x.reason_id.bypass_minimum_break
                    or x.break_hours
                    >= this.employee_id.company_id.hr_attendance_break_min_break
                ).mapped("break_hours")
            )

    @api.depends("break_hours")
    def _compute_worked_hours(self):
        """Subtract break time from work hours"""
        result = super()._compute_worked_hours()
        for this in self:
            this.worked_hours = this.worked_hours - this.break_hours
        return result

    def button_show_breaks(self):
        this = self[:1]
        return {
            "type": "ir.actions.act_window",
            "name": _("Edit breaks for %s") % this.display_name,
            "views": [(False, "tree")],
            "res_model": "hr.attendance.break",
            "domain": [("attendance_id", "=", this.id)],
            "context": {
                "default_attendance_id": this.id,
                "default_begin": this.check_in,
                "default_end": this.check_in,
            },
        }

    def write(self, vals):
        """Close open breaks if writing check_out"""
        result = super().write(vals)
        if vals.get("check_out"):
            self.mapped("break_ids").filtered(lambda x: not x.end).write(
                {"end": vals["check_out"]}
            )
        return result

    def _impose_break_prepare_data(self, begin, end):
        """
        Return a dict to create an imposed break for self
        """
        self.ensure_one()
        return {
            "attendance_id": self.id,
            "begin": max(self.check_in, begin),
            "end": min(self.check_out or datetime.max, end),
            "reason_id": self.env.ref("hr_attendance_break.reason_imposed").id,
        }

    def _impose_break(self, hours):
        """
        Add hours of break time to attendances in self, append to existing
        break(s), otherwise add it in the middle of the attendance
        """
        break_hours = hours

        def add_break(attendance, begin, end):
            return (
                self.env["hr.attendance.break"]
                .create(attendance._impose_break_prepare_data(begin, end))
                .break_hours
                if begin != end
                else 0.0
            )

        # the below might create overlapping breaks with a weird combination of
        # breaks and attendances, but we don't expect that to matter in practice
        for this in self:
            for _break in this.break_ids:
                if not _break.end:
                    _break.end = _break.begin + timedelta(seconds=1)
                break_hours -= add_break(
                    this, _break.end, _break.end + timedelta(hours=break_hours)
                )
            break_start = this.check_in + (
                timedelta(
                    hours=(this.check_out - this.check_in).total_seconds() / 3600 / 2
                    - break_hours / 2
                )
                if this.check_out and break_hours
                else timedelta(0)
            )
            break_hours -= add_break(
                this, break_start, break_start + timedelta(hours=break_hours)
            )

    def _update_overtime(self, employee_attendance_dates=None):
        """Adjust overtime with breaks taken"""
        if employee_attendance_dates is None:
            employee_attendance_dates = self._get_attendances_dates()
        attendances = self.search(
            OR(
                [
                    AND(
                        [
                            OR(
                                [
                                    [
                                        ("check_in", ">=", attendance_date[0]),
                                        (
                                            "check_in",
                                            "<",
                                            attendance_date[0] + timedelta(hours=24),
                                        ),
                                    ]
                                    for attendance_date in attendance_dates
                                ]
                            ),
                            [("employee_id", "=", employee.id)],
                        ]
                    )
                    for employee, attendance_dates in employee_attendance_dates.items()
                ]
            )
        )
        # super looks at work_hours, in some cases, at checkin, checkout in others
        # we manipulate the cache that work_hours comes back without breaks, so that
        # we can subtract the break time unconditionally below
        attendances.read(["worked_hours"])
        for attendance in attendances:
            attendance._cache["worked_hours"] += attendance.break_hours

        result = super()._update_overtime(
            employee_attendance_dates=employee_attendance_dates
        )

        attendances.invalidate_cache(["worked_hours"], attendances.ids)
        overtimes = (
            self.env["hr.attendance.overtime"]
            .sudo()
            .search(
                OR(
                    [
                        [
                            (
                                "date",
                                "in",
                                [
                                    attendance_date[1]
                                    for attendance_date in attendance_dates
                                ],
                            ),
                            ("employee_id", "=", employee.id),
                        ]
                        for employee, attendance_dates in employee_attendance_dates.items()
                    ]
                )
                + [("adjustment", "=", False)],
            )
        )
        for overtime in overtimes:
            overtime.duration -= sum(
                attendances.filtered(
                    lambda x: x.employee_id == overtime.employee_id
                    and any(
                        overtime.date == attendance_date[1]
                        and x.check_in >= attendance_date[0]
                        and x.check_in < attendance_date[0] + timedelta(hours=24)
                        for attendance_date in employee_attendance_dates[
                            overtime.employee_id
                        ]
                    )
                ).mapped("break_hours")
            )
        return result
