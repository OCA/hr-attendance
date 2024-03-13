# Copyright 2023 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)


import datetime

import pytz

from odoo import api, fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    break_state = fields.Selection(
        [("on_break", "On break"), ("no_break", "Not on break")],
        compute="_compute_break_state",
    )
    break_hours_today = fields.Float(
        compute="_compute_hours_today",
    )

    @api.depends("attendance_ids.break_ids.begin", "attendance_ids.break_ids.end")
    def _compute_break_state(self):
        for this in self:
            current_break = self._get_current_break()
            this.break_state = (
                "on_break" if current_break and not current_break.end else "no_break"
            )

    @api.depends("attendance_ids.break_ids.begin", "attendance_ids.break_ids.end")
    def _compute_presence_state(self):
        result = super()._compute_presence_state()
        for this in self:
            if this.break_state == "on_break" and this.hr_presence_state == "present":
                this.hr_presence_state = "absent"
        return result

    def _compute_hours_today(self):
        result = super()._compute_hours_today()
        now = fields.Datetime.now()
        for this in self:
            day_start, _dummy = self.env["hr.attendance"]._get_day_start_and_day(
                this, now
            )
            attendances = self.env["hr.attendance"].search(
                [
                    ("employee_id", "=", this.id),
                    ("check_in", "<=", now),
                    "|",
                    ("check_out", ">=", day_start),
                    ("check_out", "=", False),
                ]
            )
            this.break_hours_today = sum(attendances.mapped("break_hours")) + sum(
                attendances.mapped("break_ids")
                .filtered(lambda x: not x.end)
                .mapped(lambda x: x.begin and ((now - x.begin).total_seconds() / 3600))
            )
            this.hours_today -= this.break_hours_today
        return result

    def _get_current_break(self):
        HrAttendanceBreak = self.env["hr.attendance.break"].sudo()
        return HrAttendanceBreak.search(
            [
                ("attendance_id", "in", self.mapped("last_attendance_id").ids),
                ("begin", "<=", fields.Datetime.now()),
                ("end", "=", False),
            ],
            limit=1,
        )

    def attendance_manual_break(self, next_action, entered_pin=None):
        """Create break record or end currently open break"""
        now = fields.Datetime.now()
        employee = self.sudo()
        HrAttendanceBreak = self.env["hr.attendance.break"].sudo()
        current_break = self._get_current_break()

        if current_break:
            current_break.end = now
        else:
            current_break = HrAttendanceBreak.create(
                {
                    "attendance_id": employee.last_attendance_id.id,
                    "begin": now,
                }
            )
        return employee.break_state

    def _attendance_action_change(self):
        """Close possibly open breaks when closing an attendance"""
        attendance = super()._attendance_action_change()
        if attendance.check_out:
            attendance.mapped("break_ids").filtered(lambda x: not x.end).write(
                {
                    "end": attendance.check_out,
                }
            )
        return attendance

    def _check_mandatory_break_yesterday(self):
        """Run _check_mandatory_break for yesterday"""
        yesterday = fields.Date.context_today(self) - datetime.timedelta(days=1)
        for this in self:
            this._check_mandatory_break(yesterday)

    def _check_mandatory_break(self, date):
        """Run an action if an employee did not take enough break time on a working day"""
        self.ensure_one()
        day_start = (
            pytz.timezone(self.tz)
            .localize(datetime.datetime.combine(date, datetime.time.min))
            .astimezone(pytz.utc)
            .replace(tzinfo=None)
        )
        day_end = (
            pytz.timezone(self.tz)
            .localize(datetime.datetime.combine(date, datetime.time.max))
            .astimezone(pytz.utc)
            .replace(tzinfo=None)
        )
        attendances = self.env["hr.attendance"].search(
            [
                ("employee_id", "in", self.ids),
                ("check_in", ">=", day_start),
                ("check_in", "<=", day_end),
            ],
            order="check_in asc",
        )
        # TODO how do we handle attendances that span multiple days?
        work_hours = sum(attendances.mapped("worked_hours"))
        break_hours = sum(attendances.mapped("break_hours"))

        for last_attendance, attendance in zip(attendances, attendances[1:]):
            between_work = (
                attendance.check_in - last_attendance.check_out
            ).total_seconds() / 3600
            if between_work >= self.company_id.hr_attendance_break_min_break:
                break_hours += between_work

        for threshold in self.company_id.hr_attendance_break_threshold_ids.sorted(
            "min_hours", reverse=True
        ):
            if work_hours >= threshold.min_hours and break_hours < threshold.min_break:
                self._check_mandatory_break_action(
                    date, threshold, attendances, break_hours
                )
                break

    def _check_mandatory_break_action(self, date, threshold, attendances, break_hours):
        """Run an action when an employee didn't take mandatory breaks"""
        self.ensure_one()
        return (
            self.env.ref("hr_attendance_break.action_mandatory_break")
            .with_context(
                active_id=self.id,
                active_ids=self.ids,
                active_model=self._name,
                hr_attendance_break_date=date,
                hr_attendance_break_threshold=threshold,
                hr_attendance_break_attendances=attendances,
                hr_attendance_break_hours=break_hours,
            )
            .run()
        )
