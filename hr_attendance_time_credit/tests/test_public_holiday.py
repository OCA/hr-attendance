# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
"""Tests for the is_public_holiday computed field."""

from datetime import datetime

from odoo.tests.common import tagged

from .common import TestHrAttendanceTimeCreditCommon


@tagged("post_install", "-at_install")
class TestPublicHoliday(TestHrAttendanceTimeCreditCommon):
    """Tests for is_public_holiday on hr.attendance."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.calendar = cls._make_calendar(5, name="Mon-Fri PH")
        cls.employee.resource_calendar_id = cls.calendar

    def _att(self, check_in_dt, check_out_dt=None):
        return self._create_attendance(
            check_in_dt,
            check_out_dt,
            context={"skip_time_credit_recompute": True},
        )

    def test_normal_weekday_not_holiday(self):
        """Wednesday with no calendar leave → is_public_holiday=False."""
        att = self._att(datetime(2026, 1, 7, 8, 0, 0), datetime(2026, 1, 7, 16, 0, 0))
        self.assertFalse(att.is_public_holiday)

    def test_weekend_without_leave_not_holiday(self):
        """Saturday with no calendar leave → is_public_holiday=False."""
        att = self._att(datetime(2026, 1, 10, 8, 0, 0), datetime(2026, 1, 10, 16, 0, 0))
        self.assertFalse(att.is_public_holiday)

    def test_global_calendar_leave_is_holiday(self):
        """Day covered by a global calendar leave → is_public_holiday=True."""
        # Jan 1 2026 is a Thursday — add a global leave for it
        self.env["resource.calendar.leaves"].create(
            {
                "name": "New Year",
                "calendar_id": self.calendar.id,
                "resource_id": False,  # global
                "date_from": datetime(2026, 1, 1, 0, 0, 0),
                "date_to": datetime(2026, 1, 1, 23, 59, 59),
            }
        )
        att = self._att(datetime(2026, 1, 1, 8, 0, 0), datetime(2026, 1, 1, 16, 0, 0))
        self.assertTrue(att.is_public_holiday)

    def test_employee_specific_leave_not_holiday(self):
        """Employee-specific leave (resource_id != False) → is_public_holiday=False."""
        self.env["resource.calendar.leaves"].create(
            {
                "name": "Personal leave",
                "calendar_id": self.calendar.id,
                "resource_id": self.employee.resource_id.id,
                "date_from": datetime(2026, 1, 7, 0, 0, 0),
                "date_to": datetime(2026, 1, 7, 23, 59, 59),
            }
        )
        att = self._att(datetime(2026, 1, 7, 8, 0, 0), datetime(2026, 1, 7, 16, 0, 0))
        self.assertFalse(att.is_public_holiday)

    def test_midnight_crossing_holiday_segment(self):
        """Attendance spanning Dec 31 → Jan 1: Jan 1 is holiday, Dec 31 is not."""
        self.env["resource.calendar.leaves"].create(
            {
                "name": "New Year",
                "calendar_id": self.calendar.id,
                "resource_id": False,
                "date_from": datetime(2026, 1, 1, 0, 0, 0),
                "date_to": datetime(2026, 1, 1, 23, 59, 59),
            }
        )
        # Dec 31 22:00 → Jan 1 04:00
        att = self._att(datetime(2025, 12, 31, 22, 0, 0), datetime(2026, 1, 1, 4, 0, 0))
        # is_public_holiday on the attendance record itself uses check_in date
        # which is Dec 31 — not a holiday
        self.assertFalse(att.is_public_holiday)
        # But _get_day_type_for_date on Jan 1 must include is_holiday=True
        day_type, is_holiday = att._get_day_type_for_date(datetime(2026, 1, 1).date())
        self.assertTrue(is_holiday)
        day_type_dec31, is_holiday_dec31 = att._get_day_type_for_date(
            datetime(2025, 12, 31).date()
        )
        self.assertFalse(is_holiday_dec31)

    def test_no_calendar_not_holiday(self):
        """Employee with no calendar → is_public_holiday=False (safe default)."""
        self.employee.resource_calendar_id = False
        company_cal = self.company.resource_calendar_id
        self.company.resource_calendar_id = False
        try:
            att = self._att(
                datetime(2026, 1, 1, 8, 0, 0),
                datetime(2026, 1, 1, 16, 0, 0),
            )
            self.assertFalse(att.is_public_holiday)
        finally:
            self.employee.resource_calendar_id = self.calendar
            self.company.resource_calendar_id = company_cal

    def test_domain_segment_operators_on_is_public_holiday(self):
        """is_public_holiday criteria with '=', '!=' and other operators."""
        att = self._create_fixed_attendance()
        self.assertTrue(
            att._domain_matches_segment(
                "[('is_public_holiday', '=', False)]", "working_day", False
            )
        )
        self.assertFalse(
            att._domain_matches_segment(
                "[('is_public_holiday', '=', True)]", "working_day", False
            )
        )
        self.assertTrue(
            att._domain_matches_segment(
                "[('is_public_holiday', '!=', True)]", "working_day", False
            )
        )
        self.assertFalse(
            att._domain_matches_segment(
                "[('is_public_holiday', '!=', False)]", "working_day", False
            )
        )
        self.assertTrue(
            att._domain_matches_segment(
                "[('is_public_holiday', 'in', (False,))]", "working_day", False
            )
        )
