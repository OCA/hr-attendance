from datetime import date, datetime, timedelta
from unittest.mock import Mock, patch

from odoo import _, fields
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestHrAttendanceReport(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a = cls.env.ref("base.main_company")
        cls.company_b = cls.env["res.company"].create({"name": "Company B"})
        cls.department_a = cls.env["hr.department"].create(
            {"name": "Department A", "company_id": cls.company_a.id}
        )
        cls.department_b = cls.env["hr.department"].create(
            {"name": "Department B", "company_id": cls.company_b.id}
        )
        cls.employee_a = cls.env["hr.employee"].create(
            {
                "name": "Employee A",
                "company_id": cls.company_a.id,
                "department_id": cls.department_a.id,
            }
        )
        cls.employee_no_attendance = cls.env["hr.employee"].create(
            {
                "name": "Employee No Attendance",
                "company_id": cls.company_a.id,
                "department_id": cls.department_a.id,
            }
        )
        cls.employee_b = cls.env["hr.employee"].create(
            {
                "name": "Employee B",
                "company_id": cls.company_b.id,
                "department_id": cls.department_b.id,
            }
        )

    def _create_attendance(self, employee, check_in, check_out=None):
        return self.env["hr.attendance"].create(
            {
                "employee_id": employee.id,
                "check_in": check_in,
                "check_out": check_out,
            }
        )

    def _prepare_report(self, data):
        return self.env["hr.attendance.report.service"]._prepare_report_values(data)

    def _individual_data(self, **extra):
        data = {
            "report_type": "individual",
            "employee_ids": [self.employee_a.id],
            "department_ids": [],
            "company_id": self.company_a.id,
            "date_from": "2024-01-01",
            "date_to": "2024-01-01",
            "detailed": False,
            "include_open_attendances": False,
            "time_format": "hhmm",
        }
        data.update(extra)
        return data

    def _department_data(self, **extra):
        data = {
            "report_type": "department",
            "employee_ids": [],
            "department_ids": [self.department_a.id],
            "company_id": self.company_a.id,
            "date_from": "2024-01-01",
            "date_to": "2024-01-01",
            "detailed": False,
            "include_open_attendances": False,
            "time_format": "hhmm",
        }
        data.update(extra)
        return data

    def _new_wizard(self, **vals):
        values = {
            "report_type": "individual",
            "company_id": self.company_a.id,
            "employee_ids": [(6, 0, [self.employee_a.id])],
            "department_ids": [(6, 0, [self.department_a.id])],
            "date_from": fields.Date.to_date("2024-01-01"),
            "date_to": fields.Date.to_date("2024-01-02"),
            "time_format": "hhmm",
        }
        values.update(vals)
        return self.env["hr.attendance.report.wizard"].new(values)

    def test_wizard_validation_date_range(self):
        wizard = self._new_wizard(
            date_from=fields.Date.to_date("2024-01-10"),
            date_to=fields.Date.to_date("2024-01-01"),
        )
        with self.assertRaises(ValidationError):
            wizard._validate_attendance_report_fields()

    def test_wizard_validation_rejects_future_dates(self):
        tomorrow = date.today() + timedelta(days=1)
        wizard = self._new_wizard(
            date_from=tomorrow,
            date_to=tomorrow,
        )
        with self.assertRaises(ValidationError):
            wizard._validate_attendance_report_fields()

    def test_wizard_action_print_report_calls_report_action(self):
        wizard = self._new_wizard()
        report_action = Mock(return_value={"type": "ir.actions.report"})
        report_ref = Mock()
        report_ref.with_context.return_value = report_ref
        report_ref.report_action = report_action

        with patch.object(type(wizard.env), "ref", return_value=report_ref):
            result = wizard.action_print_report()

        report_ref.with_context.assert_called_once_with(tz=wizard.env.user.tz)
        self.assertEqual(result, {"type": "ir.actions.report"})

        call_args = report_action.call_args
        self.assertEqual(call_args.args[0], wizard)
        data = call_args.args[1]
        self.assertEqual(data["report_type"], "individual")
        self.assertEqual(data["employee_ids"], [self.employee_a.id])
        self.assertEqual(data["department_ids"], [self.department_a.id])
        self.assertEqual(data["company_id"], self.company_a.id)

    def test_wizard_validation_requires_employee_for_individual(self):
        wizard = self._new_wizard(employee_ids=[(5, 0, 0)])
        with self.assertRaises(ValidationError):
            wizard._validate_attendance_report_fields()

    def test_wizard_validation_requires_department_for_department_report(self):
        wizard = self._new_wizard(
            report_type="department",
            employee_ids=[(6, 0, [self.employee_a.id])],
            department_ids=[(5, 0, 0)],
        )
        with self.assertRaises(ValidationError):
            wizard._validate_attendance_report_fields()

    def test_individual_report_excludes_open_attendances(self):
        self._create_attendance(
            self.employee_a,
            datetime(2024, 1, 1, 8, 0, 0),
            None,
        )

        result = self._prepare_report(self._individual_data())

        self.assertNotIn(self.employee_a, result["lines"])
        self.assertNotIn(self.employee_a, result["totals"])

    def test_individual_report_includes_open_attendances_with_open_state(self):
        self._create_attendance(
            self.employee_a,
            datetime(2024, 1, 1, 8, 0, 0),
            None,
        )

        result = self._prepare_report(
            self._individual_data(include_open_attendances=True)
        )

        employee_lines = result["lines"][self.employee_a]
        self.assertEqual(len(employee_lines), 1)
        self.assertEqual(employee_lines[0]["state"], _("Open"))
        self.assertEqual(employee_lines[0]["worked_hours"], 0)
        self.assertEqual(result["totals"][self.employee_a]["total_attendances"], 0)

    def test_cross_midnight_attendance_is_split_in_summary(self):
        self._create_attendance(
            self.employee_a,
            datetime(2024, 1, 1, 22, 0, 0),
            datetime(2024, 1, 2, 2, 0, 0),
        )

        result = self._prepare_report(
            self._individual_data(
                date_from="2024-01-01",
                date_to="2024-01-02",
                include_open_attendances=True,
            )
        )

        employee_lines = result["lines"][self.employee_a]
        self.assertEqual(len(employee_lines), 2)
        self.assertAlmostEqual(
            sum(line["worked_hours"] for line in employee_lines),
            4.0,
            delta=0.01,
        )

    def test_summary_report_includes_empty_days_in_range(self):
        self._create_attendance(
            self.employee_a,
            datetime(2024, 1, 1, 9, 0, 0),
            datetime(2024, 1, 1, 17, 0, 0),
        )
        self._create_attendance(
            self.employee_a,
            datetime(2024, 1, 3, 9, 0, 0),
            datetime(2024, 1, 3, 17, 0, 0),
        )

        result = self._prepare_report(
            self._individual_data(
                date_from="2024-01-01",
                date_to="2024-01-03",
                include_open_attendances=True,
            )
        )

        employee_lines = result["lines"][self.employee_a]
        self.assertEqual(len(employee_lines), 3)
        empty_days = [line for line in employee_lines if line["worked_hours"] == 0]
        self.assertEqual(len(empty_days), 1)
        self.assertEqual(empty_days[0]["date"], "02/01/2024")

    def test_summary_report_ignores_days_outside_range_after_split(self):
        self._create_attendance(
            self.employee_a,
            datetime(2023, 12, 31, 22, 0, 0),
            datetime(2024, 1, 1, 2, 0, 0),
        )

        result = self._prepare_report(
            self._individual_data(
                date_from="2024-01-01",
                date_to="2024-01-01",
                include_open_attendances=True,
            )
        )

        employee_lines = result["lines"][self.employee_a]
        self.assertEqual(len(employee_lines), 1)
        self.assertEqual(employee_lines[0]["date"], "01/01/2024")

    def test_detailed_report_returns_each_record_and_totals(self):
        self._create_attendance(
            self.employee_a,
            datetime(2024, 1, 4, 9, 0, 0),
            datetime(2024, 1, 4, 11, 0, 0),
        )
        self._create_attendance(
            self.employee_a,
            datetime(2024, 1, 4, 12, 0, 0),
            None,
        )

        result = self._prepare_report(
            self._individual_data(
                date_from="2024-01-04",
                date_to="2024-01-04",
                detailed=True,
                include_open_attendances=True,
            )
        )

        employee_lines = result["lines"][self.employee_a]
        self.assertEqual(len(employee_lines), 2)
        self.assertEqual(employee_lines[0]["date"], "04/01/2024")
        self.assertSetEqual(
            {line["state"] for line in employee_lines},
            {_("Closed"), _("Open")},
        )
        self.assertEqual(result["totals"][self.employee_a]["total_days"], 1)
        self.assertEqual(result["totals"][self.employee_a]["total_attendances"], 1)

    def test_department_report_groups_by_department(self):
        self._create_attendance(
            self.employee_a,
            datetime(2024, 1, 5, 8, 0, 0),
            datetime(2024, 1, 5, 12, 0, 0),
        )

        result = self._prepare_report(
            self._department_data(
                department_ids=[self.department_a.id],
                date_from="2024-01-05",
                date_to="2024-01-05",
            )
        )

        department_lines = result["lines"][self.department_a]
        self.assertEqual(len(department_lines), 1)
        self.assertEqual(department_lines[0]["worked_days"], 1)
        self.assertEqual(result["totals"][self.department_a]["total_employees"], 1)
        self.assertEqual(result["totals"][self.department_a]["total_attendances"], 1)

    def test_department_report_applies_company_filter(self):
        self._create_attendance(
            self.employee_a,
            datetime(2024, 1, 8, 8, 0, 0),
            datetime(2024, 1, 8, 12, 0, 0),
        )
        self._create_attendance(
            self.employee_b,
            datetime(2024, 1, 8, 9, 0, 0),
            datetime(2024, 1, 8, 13, 0, 0),
        )

        result = self._prepare_report(
            self._department_data(
                department_ids=[self.department_a.id, self.department_b.id],
                date_from="2024-01-08",
                date_to="2024-01-08",
            )
        )

        self.assertIn(self.department_a, result["lines"])
        self.assertNotIn(self.department_b, result["lines"])

    def test_multi_company_report_filter(self):
        self._create_attendance(
            self.employee_b,
            datetime(2024, 1, 7, 8, 0, 0),
            datetime(2024, 1, 7, 12, 0, 0),
        )
        self._create_attendance(
            self.employee_a,
            datetime(2024, 1, 7, 9, 0, 0),
            datetime(2024, 1, 7, 13, 0, 0),
        )

        result = self._prepare_report(
            self._individual_data(
                date_from="2024-01-07",
                date_to="2024-01-07",
                employee_ids=[self.employee_a.id, self.employee_b.id],
                include_open_attendances=True,
            )
        )

        self.assertIn(self.employee_a, result["lines"])
        self.assertNotIn(self.employee_b, result["lines"])

    def test_report_model_get_report_values_includes_base_keys(self):
        attendance = self._create_attendance(
            self.employee_a,
            datetime(2024, 1, 9, 9, 0, 0),
            datetime(2024, 1, 9, 17, 0, 0),
        )
        report_model = self.env[
            "report.hr_attendance_report_pdf.report_attendance_template"
        ]
        data = self._individual_data(
            date_from="2024-01-09",
            date_to="2024-01-09",
            include_open_attendances=True,
        )

        result = report_model._get_report_values([attendance.id], data=data)

        self.assertEqual(result["doc_ids"], [attendance.id])
        self.assertEqual(result["doc_model"], "hr.attendance")
        self.assertEqual(result["tz"], self.env.user.tz)
        self.assertIn("docs", result)
        self.assertIn("lines", result)
        self.assertIn("totals", result)
        self.assertEqual(result["datas"]["report_type"], "individual")
