# © 2023 initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date, datetime, timedelta

import pytz

from odoo.tests import TransactionCase


def convert_tz(dt, *, from_tz=None, to_tz=None):
    return (
        pytz.timezone(from_tz or "UTC")
        .localize(dt)
        .astimezone(pytz.timezone(to_tz or "UTC"))
        .replace(tzinfo=None)
    )


class TestAttendance(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.employee = cls.env["hr.employee"].create(
            {
                "name": "Test Employee",
                "user_id": cls.env.user.id,
                "company_id": cls.env.company.id,
                "tz": "UTC",
            }
        )
        cls.reason = cls.env["hr.attendance.reason"].create(
            {
                "name": "Missing Attendance",
                "code": "MA",
            }
        )

    def test_attendance_creation_no_reason(self):
        self.env.company.attendance_missing_days_reason = False
        attendances_before = self.employee.attendance_ids
        self.employee._create_missing_attendances()
        attendances_after = self.employee.attendance_ids

        self.assertEqual(attendances_before, attendances_after)

    def test_attendance_creation_with_reason(self):
        self.env.company.attendance_missing_days_reason = self.reason
        attendances_before = self.employee.attendance_ids
        self.employee._create_missing_attendances()
        attendances_after = self.employee.attendance_ids

        attendances_new = attendances_after - attendances_before
        self.assertTrue(attendances_new)
        self.assertFalse(any(attendances_new.mapped("worked_hours")))

    def test_attendance_creation(self):
        self.env.company.attendance_missing_days_reason = self.reason

        attended = {date(2023, 7, 3 + offset) for offset in range(4)}
        for tz in ["Europe/Amsterdam", "Pacific/Auckland", "America/New_York"]:
            employee = self.employee.copy({"tz": tz, "name": f"Employee {tz}"})
            for offset, times in enumerate(((0, 30), (23, 30), (11, 30), (12, 30))):
                # Convert the times from the employee TZ zo UTC. 3rd is monday
                start = convert_tz(
                    datetime(2023, 7, 3 + offset, *times),
                    from_tz=tz,
                    to_tz="UTC",
                )

                # Generate a 30min attendance blocking the date
                self.env["hr.attendance"].create(
                    {
                        "employee_id": employee.id,
                        "check_in": start,
                        "check_out": start + timedelta(minutes=30),
                    }
                )

            # Cover a huge time span
            employee._create_missing_attendances(
                datetime(2023, 6, 1, 0, 0), datetime(2023, 8, 1, 0, 0)
            )

            domain = [
                ("employee_id", "=", employee.id),
                ("attendance_reason_ids", "=", self.reason.id),
            ]
            attendances = self.env["hr.attendance"].search(domain)
            self.assertTrue(attendances)
            for attendance in attendances:
                checkin = convert_tz(attendance.check_in, to_tz=tz)
                self.assertNotIn(checkin.date(), attended)

    def test_attendance_creation_during_day(self):
        self.env.company.attendance_missing_days_reason = self.reason

        start = datetime(2023, 7, 3, 12, 30)
        self.env["hr.attendance"].create(
            {
                "employee_id": self.employee.id,
                "check_in": start,
                "check_out": start + timedelta(minutes=30),
            }
        )

        attendances_before = self.employee.attendance_ids
        self.employee._create_missing_attendances(
            start - timedelta(hours=12),
            start - timedelta(minutes=30),
        )
        attendances_after = self.employee.attendance_ids

        attendances_new = attendances_after - attendances_before
        self.assertFalse(attendances_new)
