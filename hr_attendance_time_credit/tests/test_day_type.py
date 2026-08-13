# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
"""Day-type classification and public-holiday handling in one scenario each."""

from datetime import date, datetime, timedelta

from odoo.tests.common import tagged
from odoo.tools import mute_logger

from .common import TestHrAttendanceTimeCreditCommon

ATTENDANCE_LOGGER = "odoo.addons.hr_attendance_time_credit.models.hr_attendance"


@tagged("post_install", "-at_install")
class TestDayTypeAndHolidayScenario(TestHrAttendanceTimeCreditCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.calendar_monfri = cls._make_calendar(5, tz="UTC", name="Mon-Fri")
        cls.calendar_monsat = cls._make_calendar(6, tz="UTC", name="Mon-Sat")
        cls.employee.resource_calendar_id = cls.calendar_monfri

    def test_day_type_scenario(self):
        # Weekday versus weekend under a Mon-Fri calendar.
        wed = self._att_on(self.employee, date(2026, 1, 7))
        sat = self._att_on(self.employee, date(2026, 1, 3))
        self.assertEqual(wed.check_in_day_type, "working_day")
        self.assertEqual(sat.check_in_day_type, "non_working_day")
        # A calendar that includes Saturday reclassifies that same weekday.
        self.employee.resource_calendar_id = self.calendar_monsat
        self.assertEqual(
            self._att_on(self.employee, date(2026, 1, 10)).check_in_day_type,
            "working_day",
        )

        # A two-week calendar uses the week type of the target date.
        get_week_type = self.env["resource.calendar.attendance"].get_week_type
        two_weeks = self.env["resource.calendar"].create(
            {
                "name": "Friday week A",
                "company_id": self.company.id,
                "tz": "UTC",
                "two_weeks_calendar": True,
                "attendance_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Friday A",
                            "dayofweek": "4",
                            "week_type": "0",
                            "hour_from": 8,
                            "hour_to": 16,
                        },
                    )
                ],
            }
        )
        fridays = {}
        day = date(2026, 1, 2)
        while len(fridays) < 2:
            fridays.setdefault(get_week_type(day), day)
            day += timedelta(days=7)
        shift_employee = self.env["hr.employee"].create(
            {
                "name": "Shift Employee",
                "company_id": self.company.id,
                "tz": "UTC",
                "resource_calendar_id": two_weeks.id,
            }
        )
        self.assertEqual(
            self._att_on(shift_employee, fridays[0]).check_in_day_type, "working_day"
        )
        self.assertEqual(
            self._att_on(shift_employee, fridays[1]).check_in_day_type,
            "non_working_day",
        )

        # A dated calendar line only counts inside its date_from range.
        dated = self.env["resource.calendar"].create(
            {
                "name": "Dated Wednesday",
                "company_id": self.company.id,
                "tz": "UTC",
                "attendance_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Wednesday from February",
                            "dayofweek": "2",
                            "hour_from": 8,
                            "hour_to": 16,
                            "date_from": date(2026, 2, 1),
                        },
                    )
                ],
            }
        )
        dated_employee = self.env["hr.employee"].create(
            {
                "name": "Dated Employee",
                "company_id": self.company.id,
                "tz": "UTC",
                "resource_calendar_id": dated.id,
            }
        )
        self.assertEqual(
            self._att_on(dated_employee, date(2026, 1, 14)).check_in_day_type,
            "non_working_day",
        )
        self.assertEqual(
            self._att_on(dated_employee, date(2026, 2, 4)).check_in_day_type,
            "working_day",
        )

        # With no calendar anywhere the day defaults to a working day.
        company_calendar = self.company.resource_calendar_id
        self.company.resource_calendar_id = False
        no_calendar_employee = self.env["hr.employee"].create(
            {
                "name": "No Calendar Employee",
                "company_id": self.company.id,
                "tz": "UTC",
                "resource_calendar_id": False,
            }
        )
        self.assertEqual(
            self._att_on(no_calendar_employee, date(2026, 1, 3)).check_in_day_type,
            "working_day",
        )
        self.company.resource_calendar_id = company_calendar

    def test_public_holiday_scenario(self):
        holiday_type = self._new_type("Holiday mission", segment_mode="consolidate")
        self._make_rule(
            "Holiday mission",
            holiday_type,
            domain="[('is_public_holiday', '=', True)]",
            minutes_fixed=450,
            segment_mode="consolidate",
        )
        att = self._att_on(self.employee, date(2026, 1, 7))
        self.assertFalse(att.is_public_holiday)
        self.assertFalse(
            att.time_credit_ids.filtered(lambda c: c.type_id == holiday_type)
        )

        # A global leave added after the attendance flips both the flag and
        # its credit; removing it flips them back.
        leave = self.env["resource.calendar.leaves"].create(
            {
                "name": "Holiday entered later",
                "calendar_id": self.calendar_monfri.id,
                "resource_id": False,
                "date_from": datetime(2026, 1, 7, 0, 0),
                "date_to": datetime(2026, 1, 7, 23, 59, 59),
            }
        )
        att.invalidate_recordset(["is_public_holiday", "time_credit_ids"])
        self.assertTrue(att.is_public_holiday)
        self.assertEqual(
            att.time_credit_ids.filtered(lambda c: c.type_id == holiday_type).minutes,
            450,
        )
        leave.unlink()
        att.invalidate_recordset(["is_public_holiday", "time_credit_ids"])
        self.assertFalse(att.is_public_holiday)
        self.assertFalse(
            att.time_credit_ids.filtered(lambda c: c.type_id == holiday_type)
        )

        # An employee-specific leave is not a public holiday.
        self.env["resource.calendar.leaves"].create(
            {
                "name": "Personal leave",
                "calendar_id": self.calendar_monfri.id,
                "resource_id": self.employee.resource_id.id,
                "date_from": datetime(2026, 1, 8, 0, 0),
                "date_to": datetime(2026, 1, 8, 23, 59, 59),
            }
        )
        personal = self._att_on(self.employee, date(2026, 1, 8))
        self.assertFalse(personal.is_public_holiday)

        # A holiday on the second day of a midnight-crossing attendance is
        # visible per segment even though the stored flag follows check-in.
        self.env["resource.calendar.leaves"].create(
            {
                "name": "New Year",
                "calendar_id": self.calendar_monfri.id,
                "resource_id": False,
                "date_from": datetime(2026, 1, 1, 0, 0),
                "date_to": datetime(2026, 1, 1, 23, 59, 59),
            }
        )
        crossing = self._create_attendance(
            datetime(2025, 12, 31, 22, 0), datetime(2026, 1, 1, 4, 0)
        )
        self.assertFalse(crossing.is_public_holiday)
        self.assertTrue(crossing._get_day_type_for_date(date(2026, 1, 1))[1])
        self.assertFalse(crossing._get_day_type_for_date(date(2025, 12, 31))[1])

        # Segment domains keep their OR / negation / in / not-in semantics.
        or_domain = (
            "['|', ('check_in_day_type', '=', 'non_working_day'),"
            " ('is_public_holiday', '=', True)]"
        )
        self.assertFalse(att._domain_matches_segment(or_domain, "working_day", False))
        self.assertTrue(att._domain_matches_segment(or_domain, "working_day", True))
        self.assertTrue(
            att._domain_matches_segment(or_domain, "non_working_day", False)
        )
        negated = "['!', ('check_in_day_type', '=', 'working_day')]"
        self.assertTrue(att._domain_matches_segment(negated, "non_working_day", False))
        self.assertFalse(att._domain_matches_segment(negated, "working_day", False))
        self.assertTrue(
            att._domain_matches_segment(
                "[('check_in_day_type', 'in', ['working_day'])]", "working_day", False
            )
        )
        self.assertFalse(
            att._domain_matches_segment(
                "[('is_public_holiday', 'not in', [True])]", "working_day", True
            )
        )
        self.assertTrue(
            self.env["hr.attendance"]._segment_leaf_matches(
                "working_day", "in", ("working_day",)
            )
        )
        with mute_logger(ATTENDANCE_LOGGER):
            self.assertFalse(att._domain_matches_segment("INVALID", "working_day"))
