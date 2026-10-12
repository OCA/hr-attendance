from odoo import api, fields, models


class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    attendance_hours = fields.Float(
        compute="_compute_attendance_hours",
        digits=(16, 2),
        help="Total hours the employee was present according to "
        "HR Attendance (turnstile/biometric) on this date.",
    )
    daily_timesheet_hours = fields.Float(
        compute="_compute_attendance_hours",
        digits=(16, 2),
        help="Total timesheet hours for this employee on this date.",
    )
    attendance_status = fields.Selection(
        [
            ("ok", "OK"),
            ("warn", "~"),
            ("over", "OVER"),
            ("none", "-"),
        ],
        compute="_compute_attendance_hours",
        help="Compares total daily timesheet vs attendance hours.",
    )

    @api.depends("employee_id", "date", "unit_amount")
    def _compute_attendance_hours(self):
        emp_ids = set()
        dates = set()
        for line in self:
            if line.employee_id and line.date:
                emp_ids.add(line.employee_id.id)
                dates.add(line.date)

        if not emp_ids or not dates:
            for line in self:
                line.attendance_hours = 0.0
                line.daily_timesheet_hours = 0.0
                line.attendance_status = "none"
            return

        tz = self.env.user.tz or "UTC"

        self.env.cr.execute(
            """
            SELECT
                employee_id,
                (check_in AT TIME ZONE 'UTC' AT TIME ZONE %(tz)s)::date AS att_date,
                SUM(worked_hours) AS total_hours
            FROM hr_attendance
            WHERE
                check_out IS NOT NULL
                AND employee_id IN %(emp_ids)s
                AND (check_in AT TIME ZONE 'UTC' AT TIME ZONE %(tz)s)::date
                    IN %(dates)s
            GROUP BY employee_id, att_date
            """,
            {"tz": tz, "emp_ids": tuple(emp_ids), "dates": tuple(dates)},
        )
        att_map = {(row[0], row[1]): row[2] or 0.0 for row in self.env.cr.fetchall()}

        self.env.cr.execute(
            """
            SELECT
                employee_id,
                date,
                SUM(unit_amount) AS total_hours
            FROM account_analytic_line
            WHERE
                employee_id IN %(emp_ids)s
                AND date IN %(dates)s
                AND project_id IS NOT NULL
            GROUP BY employee_id, date
            """,
            {"emp_ids": tuple(emp_ids), "dates": tuple(dates)},
        )
        ts_map = {(row[0], row[1]): row[2] or 0.0 for row in self.env.cr.fetchall()}

        for line in self:
            if line.employee_id and line.date:
                key = (line.employee_id.id, line.date)
                att = att_map.get(key, 0.0)
                ts = ts_map.get(key, 0.0)
                line.attendance_hours = att
                line.daily_timesheet_hours = ts
                if att <= 0:
                    line.attendance_status = "none"
                elif att < ts:
                    line.attendance_status = "over"
                elif att < ts + 0.5:
                    line.attendance_status = "warn"
                else:
                    line.attendance_status = "ok"
            else:
                line.attendance_hours = 0.0
                line.daily_timesheet_hours = 0.0
                line.attendance_status = "none"
