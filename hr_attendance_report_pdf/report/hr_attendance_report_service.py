import copy
from collections import Counter
from datetime import datetime, timedelta

from odoo import _, api, fields, models


class HrAttendanceReportService(models.AbstractModel):
    _name = "hr.attendance.report.service"
    _description = "HR Attendance Report Service"

    def _prepare_report_values(self, data):
        data = self._normalize_data(data)

        if data["report_type"] == "individual":
            docs, lines = self._get_attendance_by_employees(data)
        else:
            docs, lines = self._get_attendance_by_departments(data)

        totals = self._get_totals(data, lines, docs)
        return {
            "docs": docs,
            "lines": lines,
            "totals": totals,
            "datas": data,
        }

    @api.model
    def _normalize_data(self, data):
        employee = self.env["hr.employee"]
        department = self.env["hr.department"]
        company = self.env["res.company"]
        data.update(
            {
                "employee_ids": employee.browse(data["employee_ids"]),
                "department_ids": department.browse(data["department_ids"]),
                "company_id": company.browse(data["company_id"]),
            }
        )
        return data

    def _get_totals(self, data, lines, docs=None):
        if data["report_type"] == "individual":
            if data["detailed"]:
                totals = {}
                for employee, attendances in lines.items():
                    counter = Counter(att["date"] for att in attendances)
                    totals[employee] = {
                        "total_worked_hours": sum(
                            line["worked_hours"] for line in attendances
                        ),
                        "total_days": len(counter),
                        "total_attendances": len(
                            [line for line in attendances if line["worked_hours"] > 0]
                        ),
                    }
                return totals
            else:
                totals = {}
                for employee, attendances in lines.items():
                    totals[employee] = {
                        "total_worked_hours": sum(
                            att["worked_hours"] for att in attendances
                        ),
                        "total_days": len(attendances),
                        "total_attendances": len(
                            [att for att in attendances if att["worked_hours"] > 0]
                        ),
                    }
                return totals
        else:
            totals = {}
            for department, attendances in lines.items():
                totals[department] = {
                    "total_workcenter_hours": sum(
                        line["total_worked_hours"]
                        for line in attendances
                        if line["total_worked_hours"]
                    ),
                    "total_employees": len(attendances),
                    "total_attendances": sum(
                        len([att for att in line["attendances"] if att])
                        for line in attendances
                    ),
                }
            return totals

    def _split_cross_midnight(self, attendance):
        check_in = fields.Datetime.context_timestamp(
            self.with_context(tz=self.env.user.tz), attendance.check_in
        )
        check_out = fields.Datetime.context_timestamp(
            self.with_context(tz=self.env.user.tz), attendance.check_out
        )
        end = check_in.replace(hour=23, minute=59, second=59)
        next_day = check_out.replace(hour=0, minute=0, second=0)
        return {
            attendance.check_in.date(): {
                "check_in": check_in,
                "check_out": end,
                "worked_hours": (end - check_in).total_seconds() / 3600,
            },
            next_day.date(): {
                "check_in": next_day,
                "check_out": check_out,
                "worked_hours": (check_out - next_day).total_seconds() / 3600,
            },
        }

    def _get_attendance_by_departments(self, data):
        hr_attendance = self.env["hr.attendance"]
        hr_department = self.env["hr.department"]
        query = """
            SELECT
                e.name                        AS employee_name,
                e.department_id               AS department_id,
                ARRAY_AGG(att.id)             AS attendances,
                SUM(att.worked_hours)         AS total_worked_hours,
                COUNT(att.id)                 AS total_records
            FROM hr_employee e
            LEFT JOIN hr_attendance att
                ON att.employee_id = e.id
            WHERE e.department_id in %s
                AND att.check_in::date  >= %s
                AND att.check_out::date <= %s
            GROUP BY e.id, e.name
            ORDER BY e.name DESC;
        """
        params = [tuple(data["department_ids"].ids), data["date_from"], data["date_to"]]
        if data["company_id"]:
            query = query.replace("WHERE", "WHERE e.company_id = %s AND")
            params.insert(0, data["company_id"].id)

        self.env.cr.execute(query, tuple(params))
        employees = self.env.cr.dictfetchall()
        attendances_by_departments = {}

        for employee in employees:
            worked_days = set()
            department_id = hr_department.browse(employee["department_id"])
            attendances_by_departments.setdefault(department_id, [])
            for att in employee["attendances"]:
                attendance = hr_attendance.browse(att)
                if attendance.check_in:
                    date = attendance.check_in.date()
                    worked_days.add(date)
            employee.update(
                {
                    "worked_days": len(worked_days),
                }
            )
            attendances_by_departments[department_id].append(employee)

        return hr_attendance, attendances_by_departments

    def _fetch_attendance_records(self, data):
        query = """
            SELECT att.id
            FROM hr_attendance att
            JOIN hr_employee emp ON emp.id = att.employee_id
            WHERE att.employee_id in %s
            AND (att.check_in::date BETWEEN %s AND %s
            OR att.check_out::date BETWEEN %s AND %s)
            ORDER BY att.check_in ASC;
        """
        params = [
            tuple(data["employee_ids"].ids),
            data["date_from"],
            data["date_to"],
            data["date_from"],
            data["date_to"],
        ]

        if data.get("company_id"):
            query = query.replace("WHERE", "WHERE emp.company_id = %s AND")
            params.insert(0, data["company_id"].id)

        self.env.cr.execute(query, tuple(params))
        ids = [row[0] for row in self.env.cr.fetchall()]
        attendance_ids = self.env["hr.attendance"].browse(ids)

        if not data.get("include_open_attendances"):
            attendance_ids = attendance_ids.filtered(lambda a: a.check_out)

        return attendance_ids

    def _process_detailed_attendances(self, attendance_ids):
        attendances_by_employee = {}
        for attendance in attendance_ids:
            attendances_by_employee.setdefault(attendance.employee_id, []).append(
                {
                    "date": attendance.check_in.date().strftime("%d/%m/%Y"),
                    "check_in": attendance.check_in,
                    "check_out": attendance.check_out,
                    "worked_hours": attendance.worked_hours,
                    "state": _("Open") if not attendance.check_out else _("Closed"),
                }
            )
        return attendances_by_employee

    def _process_summary_attendances(self, attendance_ids, data):
        date_from = datetime.strptime(data["date_from"], "%Y-%m-%d").date()
        date_to = datetime.strptime(data["date_to"], "%Y-%m-%d").date()

        groups = {}
        current_date = date_from
        while current_date <= date_to:
            groups.setdefault(current_date, [])
            current_date += timedelta(days=1)

        employees = {}
        tz_env = self.with_context(tz=self.env.user.tz)

        for attendance in attendance_ids:
            employees.setdefault(attendance.employee_id, copy.deepcopy(groups))
            check_in = fields.Datetime.context_timestamp(
                tz_env, attendance.check_in
            ).date()

            if not attendance.check_out:
                employees[attendance.employee_id].setdefault(check_in, []).append(
                    {
                        "check_in": check_in,
                        "check_out": False,
                        "worked_hours": attendance.worked_hours,
                    }
                )
                continue

            check_out = fields.Datetime.context_timestamp(
                tz_env, attendance.check_out
            ).date()

            if check_in != check_out:
                values = self._split_cross_midnight(attendance)
                for date, vals in values.items():
                    employees[attendance.employee_id].setdefault(date, []).append(vals)
                continue

            employees[attendance.employee_id].setdefault(check_in, []).append(
                {
                    "check_in": check_in,
                    "check_out": check_out,
                    "worked_hours": attendance.worked_hours,
                }
            )

        attendances_by_employee = {}
        for employee, emp_groups in employees.items():
            attendances_by_employee[employee] = []
            for group_date, att_list in emp_groups.items():
                if not (date_from <= group_date <= date_to):
                    continue

                if not att_list:
                    att_list = [
                        {"check_in": None, "check_out": None, "worked_hours": 0}
                    ]

                state_val = (
                    _("Open")
                    if (
                        att_list[0].get("check_in")
                        and not att_list[-1].get("check_out")
                    )
                    else _("Closed")
                )

                attendances_by_employee[employee].append(
                    {
                        "date": group_date.strftime("%d/%m/%Y"),
                        "worked_hours": sum(a["worked_hours"] for a in att_list) or 0,
                        "state": state_val,
                    }
                )

        return attendances_by_employee

    def _get_attendance_by_employees(self, data):
        attendance_ids = self._fetch_attendance_records(data)
        if data.get("detailed"):
            attendances_by_employee = self._process_detailed_attendances(attendance_ids)
        else:
            attendances_by_employee = self._process_summary_attendances(
                attendance_ids, data
            )
        return attendance_ids, attendances_by_employee
