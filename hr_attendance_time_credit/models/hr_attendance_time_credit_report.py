# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class HrAttendanceTimeCreditReport(models.Model):
    _name = "hr.attendance.time.credit.report"
    _description = "Attendance Time Credit Monthly Report"
    _auto = False
    _order = "employee_id, month desc"

    employee_id = fields.Many2one("hr.employee", readonly=True)
    company_id = fields.Many2one("res.company", readonly=True)
    month = fields.Date(
        readonly=True,
        help="First day of the month this row covers.",
    )
    worked_hours = fields.Float(
        readonly=True,
        digits=(16, 2),
        help="Total worked hours for closed attendances in this month.",
    )
    total_credited_minutes = fields.Integer(
        readonly=True,
        help="Total time credit minutes granted in this month.",
    )
    credited_hours = fields.Float(
        readonly=True,
        digits=(16, 2),
        help="Total credited minutes expressed in hours.",
    )
    total_hours = fields.Float(
        string="Total Hours (Worked + Credited)",
        readonly=True,
        digits=(16, 2),
        help="Worked hours plus credited hours for this month.",
    )
    attendance_count = fields.Integer(
        readonly=True,
        help="Number of closed attendance records in this month.",
    )

    def init(self):
        self.env.cr.execute("DROP VIEW IF EXISTS hr_attendance_time_credit_report")
        self.env.cr.execute(
            """
            CREATE OR REPLACE VIEW hr_attendance_time_credit_report AS
                SELECT
                    (
                        hashtext(
                            att.employee_id::text || '-'
                            || date_trunc('month', att.check_in)::text
                        )::bigint & 9223372036854775807
                    ) % 2147483647 AS id,
                    att.employee_id,
                    emp.company_id,
                    date_trunc('month', att.check_in)::date AS month,
                    SUM(att.worked_hours) AS worked_hours,
                    COALESCE(SUM(tc.credited_minutes), 0)
                        AS total_credited_minutes,
                    COALESCE(SUM(tc.credited_minutes), 0) / 60.0
                        AS credited_hours,
                    SUM(att.worked_hours)
                        + COALESCE(SUM(tc.credited_minutes), 0) / 60.0
                        AS total_hours,
                    COUNT(DISTINCT att.id) AS attendance_count
                FROM hr_attendance att
                LEFT JOIN hr_employee emp ON att.employee_id = emp.id
                LEFT JOIN (
                    SELECT
                        attendance_id,
                        SUM(minutes) AS credited_minutes
                    FROM hr_attendance_time_credit
                    GROUP BY attendance_id
                ) tc ON tc.attendance_id = att.id
                WHERE att.check_out IS NOT NULL
                GROUP BY
                    att.employee_id,
                    emp.company_id,
                    date_trunc('month', att.check_in)
        """
        )
