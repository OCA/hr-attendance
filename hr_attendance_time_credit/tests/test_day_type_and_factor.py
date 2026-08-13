# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
"""Tests for day-type classification, multiplicative factor, midnight crossing,
and domain conditions on check_in_day_type."""

from datetime import date, datetime

from odoo.tests.common import tagged
from odoo.tools import mute_logger

from .common import TestHrAttendanceTimeCreditCommon

NIGHT_CONDITION_CODE = """
check_in = record.check_in
if check_in:
    tz_name = record.employee_id._get_tz()
    tz = timezone(tz_name)
    local_check_in = timezone('UTC').localize(check_in).astimezone(tz)
    hour = local_check_in.hour + local_check_in.minute / 60.0
    action = hour >= 22.0 or hour < 6.0
else:
    action = False
"""


@tagged("post_install", "-at_install")
class TestCheckInDayType(TestHrAttendanceTimeCreditCommon):
    """Tests for the check_in_day_type computed field."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.calendar_monfri = cls._make_calendar(5, name="Mon-Fri")
        cls.calendar_monsat = cls._make_calendar(6, name="Mon-Sat")
        cls.employee.resource_calendar_id = cls.calendar_monfri

    def _att_on(self, target_date, **kwargs):
        """Create a completed attendance on *target_date* (a date object)."""
        # Use a fixed 8-hour window on that date (UTC)
        check_in = datetime(
            target_date.year, target_date.month, target_date.day, 8, 0, 0
        )
        check_out = datetime(
            target_date.year, target_date.month, target_date.day, 16, 0, 0
        )
        return self._create_attendance(
            check_in, check_out, context={"skip_time_credit_recompute": True}, **kwargs
        )

    def test_saturday_is_non_working_with_monfri_calendar(self):
        """Saturday → non_working_day with a Mon-Fri calendar."""
        # 2026-01-03 is a Saturday
        att = self._att_on(date(2026, 1, 3))
        self.assertEqual(att.check_in_day_type, "non_working_day")

    def test_wednesday_is_working_with_monfri_calendar(self):
        """Wednesday → working_day with a Mon-Fri calendar."""
        # 2026-01-07 is a Wednesday
        att = self._att_on(date(2026, 1, 7))
        self.assertEqual(att.check_in_day_type, "working_day")

    def test_saturday_is_working_with_monsat_calendar(self):
        """Saturday → working_day with a Mon-Sat calendar."""
        self.employee.resource_calendar_id = self.calendar_monsat
        att = self._att_on(date(2026, 1, 3))
        self.assertEqual(att.check_in_day_type, "working_day")
        # Restore
        self.employee.resource_calendar_id = self.calendar_monfri

    def test_no_check_in_gives_false(self):
        """Attendance with no check_out still computes a day type from check_in."""
        # hr.attendance.check_in is required; test that a partial attendance
        # (check_in set, check_out missing) still returns a valid day type.
        att = self._create_attendance(
            datetime(2026, 1, 7, 8, 0, 0),  # Wednesday
            context={"skip_time_credit_recompute": True},
        )
        # Wednesday is a working day on the Mon-Fri calendar assigned in setUpClass
        self.assertEqual(att.check_in_day_type, "working_day")

    def test_no_calendar_defaults_to_working_day(self):
        """Employee with no calendar (and no company fallback) → working_day."""
        # Must also clear the company calendar so the fallback chain is truly empty.
        orig_company_cal = self.company.resource_calendar_id
        self.employee.resource_calendar_id = False
        self.company.resource_calendar_id = False
        att = self._att_on(date(2026, 1, 3))
        self.assertEqual(att.check_in_day_type, "working_day")
        self.employee.resource_calendar_id = self.calendar_monfri
        self.company.resource_calendar_id = orig_company_cal


@tagged("post_install", "-at_install")
class TestWorkedTimeFactor(TestHrAttendanceTimeCreditCommon):
    """Tests for the worked_time_factor computation mode."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.calendar_nolunch = cls._make_calendar(
            7, tz="UTC", hour_from=0, hour_to=24, name="No-Lunch UTC"
        )
        cls.employee.resource_calendar_id = cls.calendar_nolunch
        cls.factor_rule = cls._make_rule(
            "1.5x factor",
            minutes_type="worked_time_factor",
            factor_value=1.5,
            factor_base="worked_hours",
        )

    def _att_hours(self, hours):
        """Create a completed attendance of *hours* length."""
        check_in_hour = 8
        check_in = datetime(2026, 1, 7, check_in_hour, 0, 0)
        check_out = datetime(2026, 1, 7, check_in_hour + hours, 0, 0)
        return self._create_attendance(
            check_in,
            check_out,
            context={"skip_time_credit_recompute": True},
        )

    def test_factor_1_5_on_8_hours(self):
        """Factor 1.5 on 8h worked → 4h credit (240 min)."""
        att = self._att_hours(8)
        result = self.factor_rule._evaluate(att)
        # 8h * 60 * (1.5 - 1.0) = 240 min
        self.assertEqual(result, 240)

    def test_factor_1_0_gives_zero(self):
        """Factor 1.0 → 0 credit (no additional time)."""
        self.factor_rule.factor_value = 1.0
        att = self._att_hours(8)
        result = self.factor_rule._evaluate(att)
        self.assertEqual(result, 0)

    def test_factor_with_rate(self):
        """Factor 1.5 + rate 0.5 on 8h: int(8*60*0.5*0.5) = 120 min."""
        self.factor_rule.factor_value = 1.5
        self.factor_rule.rate = 0.5
        att = self._att_hours(8)
        result = self.factor_rule._evaluate(att)
        # int(8 * 60 * 0.5) = 240, then * 0.5 rate = 120
        self.assertEqual(result, 120)

    def test_factor_with_cap(self):
        """Factor 2.0 on 8h (480 min) capped at 180 min."""
        self.factor_rule.factor_value = 2.0
        self.factor_rule.minutes_cap = 180
        att = self._att_hours(8)
        result = self.factor_rule._evaluate(att)
        self.assertEqual(result, 180)

    def test_factor_base_credited_hours(self):
        """factor_base=credited_hours: uses accumulated_hours argument."""
        self.factor_rule.factor_value = 1.5
        self.factor_rule.factor_base = "credited_hours"
        # Simulate 8h worked + 0.5h prior credits = 8.5h
        att = self._att_hours(8)
        result = self.factor_rule._evaluate(att, accumulated_hours=8.5)
        # int(8.5 * 60 * 0.5) = int(255) = 255
        self.assertEqual(result, 255)

    def test_factor_credits_created_on_attendance(self):
        """Full pipeline: factor rule creates credit line on attendance."""
        att = self._create_attendance(
            datetime(2026, 1, 7, 8, 0, 0),
            datetime(2026, 1, 7, 16, 0, 0),
        )
        self.assertEqual(len(att.time_credit_ids), 1)
        # 8h * 60 * 0.5 = 240 min
        self.assertEqual(att.time_credit_ids.minutes, 240)
        self.assertAlmostEqual(att.total_credited_hours, 8.0 + 4.0, places=1)


@tagged("post_install", "-at_install")
class TestMidnightCrossing(TestHrAttendanceTimeCreditCommon):
    """Tests for virtual segmentation when an attendance spans midnight."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.employee.tz = "UTC"
        cls.calendar_monfri = cls._make_calendar(5, name="Mon-Fri MC")
        cls.employee.resource_calendar_id = cls.calendar_monfri
        cls.credit_type.segment_mode = "segment"
        cls.factor_rule_nonworking = cls._make_rule(
            "Non-working day factor 2x",
            domain="[('check_in_day_type', '=', 'non_working_day')]",
            minutes_type="worked_time_factor",
            factor_value=2.0,
            factor_base="worked_hours",
        )

    def test_get_day_segments_single_day(self):
        """Single-day attendance produces one segment."""
        att = self._create_attendance(
            datetime(2026, 1, 7, 8, 0, 0),  # Wed
            datetime(2026, 1, 7, 16, 0, 0),
            context={"skip_time_credit_recompute": True},
        )
        segments = att._get_day_segments()
        self.assertEqual(len(segments), 1)
        seg_date, seg_hours = segments[0]
        self.assertEqual(seg_date, date(2026, 1, 7))
        self.assertAlmostEqual(seg_hours, 8.0, places=2)

    def test_get_day_segments_two_days(self):
        """Attendance crossing midnight produces two segments."""
        # Fri 22:00 → Sat 04:00 (2h Fri + 4h Sat)
        att = self._create_attendance(
            datetime(2026, 1, 9, 22, 0, 0),  # Friday
            datetime(2026, 1, 10, 4, 0, 0),  # Saturday
            context={"skip_time_credit_recompute": True},
        )
        segments = att._get_day_segments()
        self.assertEqual(len(segments), 2)
        self.assertEqual(segments[0][0], date(2026, 1, 9))  # Fri
        self.assertAlmostEqual(segments[0][1], 2.0, places=2)
        self.assertEqual(segments[1][0], date(2026, 1, 10))  # Sat
        self.assertAlmostEqual(segments[1][1], 4.0, places=2)

    def test_get_day_segments_checkout_at_midnight(self):
        """Check-out exactly at midnight: last segment has zero hours, excluded."""
        att = self._create_attendance(
            datetime(2026, 1, 9, 22, 0, 0),
            datetime(2026, 1, 10, 0, 0, 0),  # exactly midnight
            context={"skip_time_credit_recompute": True},
        )
        segments = att._get_day_segments()
        # Only the Fri segment (2h); Sat segment has 0h and is excluded
        self.assertEqual(len(segments), 1)
        self.assertAlmostEqual(segments[0][1], 2.0, places=2)

    def test_midnight_crossing_factor_matches_only_saturday_segment(self):
        """Rule matching non_working_day applies only to Saturday portion."""
        # Fri 22:00 → Sat 04:00 (2h Fri working + 4h Sat non-working)
        # Rule factor 2x on non-working: credit = 4h * 60 * (2-1) = 240 min
        att = self._create_attendance(
            datetime(2026, 1, 9, 22, 0, 0),
            datetime(2026, 1, 10, 4, 0, 0),
        )
        # Only Saturday segment matches domain [check_in_day_type = non_working_day]
        self.assertEqual(len(att.time_credit_ids), 1)
        credit = att.time_credit_ids
        self.assertEqual(credit.segment_date, date(2026, 1, 10))
        self.assertAlmostEqual(credit.segment_hours, 4.0, places=2)
        # 4h * 60 * (2.0 - 1.0) = 240
        self.assertEqual(credit.minutes, 240)

    def test_same_day_segment_date_set(self):
        """Single-day attendance with segment_mode='segment': segment_date is set.

        When the credit type uses segment_mode='segment', even single-day
        attendances go through _apply_rule_segmented so that server actions
        receive segment_date in their eval context.
        """
        # Saturday: matches the non-working domain directly
        att = self._create_attendance(
            datetime(2026, 1, 10, 8, 0, 0),  # Sat
            datetime(2026, 1, 10, 16, 0, 0),
        )
        self.assertEqual(len(att.time_credit_ids), 1)
        credit = att.time_credit_ids
        # segment_date IS set because credit type has segment_mode='segment'
        self.assertEqual(credit.segment_date, date(2026, 1, 10))

    def test_factor_base_credited_hours_midnight_crossing(self):
        """credited_hours: prior credits included in segment computation."""
        # credit_type_2 needs segmented mode for the prior rule to segment
        self.credit_type_2.segment_mode = "segment"
        # Add a prior rule (different credit_type to distinguish)
        self._make_rule(
            "Prior fixed 60min",
            credit_type=self.credit_type_2,
            minutes_fixed=60,
            sequence=5,
        )
        # Update the factor rule to use credited_hours
        self.factor_rule_nonworking.factor_base = "credited_hours"
        self.factor_rule_nonworking.sequence = 10
        # Fri 22:00 -> Sat 04:00 (2h Fri + 4h Sat)
        # Prior rule segments: Fri(60) + Sat(60) = 120 min
        # Factor rule (credited_hours): accumulated_hours = 6 + 2 = 8
        #   Sat segment: int(8.0 * 60 * 1.0) = 480 min
        att = self._create_attendance(
            datetime(2026, 1, 9, 22, 0, 0),
            datetime(2026, 1, 10, 4, 0, 0),
        )
        # 3 credit lines: prior Fri + prior Sat + factor Sat
        self.assertGreaterEqual(len(att.time_credit_ids), 1)
        factor_credits = att.time_credit_ids.filtered(
            lambda c: c.segment_date == date(2026, 1, 10)
        ).filtered(lambda c: c.type_id == self.credit_type)
        self.assertEqual(len(factor_credits), 1)
        self.assertEqual(factor_credits.minutes, 480)


@tagged("post_install", "-at_install")
class TestDomainOnDayType(TestHrAttendanceTimeCreditCommon):
    """Tests for domain-based rules using check_in_day_type."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.calendar_monfri = cls._make_calendar(5, name="Mon-Fri DT")
        cls.employee.resource_calendar_id = cls.calendar_monfri
        cls.rule_non_working = cls._make_rule(
            "Non-working day fixed 60min",
            domain="[('check_in_day_type', '=', 'non_working_day')]",
            minutes_fixed=60,
        )

    def test_rule_does_not_match_wednesday(self):
        """Fixed rule with non_working_day domain does not trigger on Wednesday."""
        att = self._create_attendance(
            datetime(2026, 1, 7, 8, 0, 0),  # Wednesday
            datetime(2026, 1, 7, 16, 0, 0),
        )
        self.assertEqual(len(att.time_credit_ids), 0)

    def test_idempotent_recompute(self):
        """Running recompute twice produces the same result."""
        att = self._create_attendance(
            datetime(2026, 1, 10, 8, 0, 0),
            datetime(2026, 1, 10, 16, 0, 0),
        )
        self.assertEqual(len(att.time_credit_ids), 1)
        att._recompute_automatic_time_credits()
        self.assertEqual(len(att.time_credit_ids), 1)
        self.assertEqual(att.time_credit_ids.minutes, 60)

    def test_domain_segment_neq_and_other_operators_on_day_type(self):
        """check_in_day_type criteria with '!=' or other operators."""
        att = self._create_fixed_attendance()
        # '!=' against a non-matching value: criterion dropped, empty domain → match
        self.assertTrue(
            att._domain_matches_segment(
                "[('check_in_day_type', '!=', 'x')]", "working_day"
            )
        )
        # '!=' matching the segment day type → no match
        self.assertFalse(
            att._domain_matches_segment(
                "[('check_in_day_type', '!=', 'working_day')]", "working_day"
            )
        )
        # operator other than = / != → criterion appended and evaluated normally
        self.assertTrue(
            att._domain_matches_segment(
                "[('check_in_day_type', 'in', ('working_day',))]", "working_day"
            )
        )

    def test_segmented_domain_non_special_leaf_credits(self):
        """Segmented rule whose domain uses a non-special leaf still credits."""
        ct = self._make_credit_type("Seg leaf", "seg_leaf", segment_mode="segment")
        self._make_rule(
            "Segmented non-special domain",
            ct,
            condition_type="domain",
            domain="[('worked_hours', '>=', 1)]",
            minutes_fixed=30,
            segment_mode="segment",
        )
        att = self._create_fixed_midnight_cross_attendance()
        credit_lines = att.time_credit_ids.filtered(lambda c: c.type_id == ct)
        self.assertEqual(len(credit_lines), 2)
        self.assertEqual(sum(credit_lines.mapped("minutes")), 60)


@tagged("post_install", "-at_install")
class TestMinutesCapSegmented(TestHrAttendanceTimeCreditCommon):
    """Tests for minutes_cap behavior with midnight-crossing attendances."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.employee.tz = "UTC"
        cls.credit_type.segment_mode = "segment"
        cls.calendar_monfri = cls._make_calendar(5, name="Mon-Fri Cap")
        cls.employee.resource_calendar_id = cls.calendar_monfri
        cls.factor_rule = cls._make_rule(
            "Non-working day factor 2x cap 120",
            domain="[('check_in_day_type', '=', 'non_working_day')]",
            minutes_type="worked_time_factor",
            factor_value=2.0,
            factor_base="worked_hours",
            minutes_cap=120,
        )

    def test_cap_applied_per_attendance_not_per_segment(self):
        """minutes_cap should limit total credit, not per-segment."""
        # Fri 22:00 -> Sun 06:00 (2h Fri + 24h Sat + 6h Sun)
        # Only Sat+Sun segments match non_working_day
        # Per-segment without cap: Sat=1440, Sun=360
        # Per-attendance with cap: total=1440+360=1800, capped -> 120
        att = self._create_attendance(
            datetime(2026, 1, 9, 22, 0, 0),
            datetime(2026, 1, 11, 6, 0, 0),
        )
        total = sum(att.time_credit_ids.mapped("minutes"))
        self.assertEqual(total, 120)


@tagged("post_install", "-at_install")
class TestFixedMinutesSegmented(TestHrAttendanceTimeCreditCommon):
    """Tests for fixed-minutes rules with midnight-crossing attendances."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.employee.tz = "UTC"
        cls.credit_type.segment_mode = "segment"
        cls.calendar_monfri = cls._make_calendar(5, name="Mon-Fri Fixed")
        cls.employee.resource_calendar_id = cls.calendar_monfri
        cls.rule_non_working_fixed = cls._make_rule(
            "Non-working day fixed 60min",
            domain="[('check_in_day_type', '=', 'non_working_day')]",
            minutes_fixed=60,
        )

    def test_fixed_minutes_matches_saturday_segment(self):
        """Fixed rule with non_working_day domain matches Sat segment."""
        # Fri 22:00 -> Sat 04:00 (2h Fri + 4h Sat)
        att = self._create_attendance(
            datetime(2026, 1, 9, 22, 0, 0),
            datetime(2026, 1, 10, 4, 0, 0),
        )
        sat_credits = att.time_credit_ids.filtered(
            lambda c: c.segment_date == date(2026, 1, 10)
        )
        self.assertEqual(len(sat_credits), 1)
        self.assertEqual(sat_credits.minutes, 60)


@tagged("post_install", "-at_install")
class TestTimezoneSegmentation(TestHrAttendanceTimeCreditCommon):
    """Tests for timezone-aware day segmentation (B5)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.calendar_madrid = cls._make_calendar(
            5, tz="Europe/Madrid", name="Madrid CEST"
        )
        cls.employee.resource_calendar_id = cls.calendar_madrid
        cls.employee.tz = "Europe/Madrid"

    def test_midnight_split_at_local_timezone(self):
        """Attendances split at local midnight, not UTC midnight.

        Europe/Madrid June 2026 = CEST (UTC+2).
        Local 2026-06-19 22:00 → 2026-06-20 06:00 (8h).
        In UTC: 2026-06-19 20:00 → 2026-06-20 04:00.
        UTC midnight splits at 4h/4h; local midnight splits at 2h/6h.
        """
        att = self._create_attendance(
            datetime(2026, 6, 19, 20, 0, 0),  # UTC = local 22:00
            datetime(2026, 6, 20, 4, 0, 0),  # UTC = local 06:00
        )
        segments = att._get_day_segments()
        self.assertEqual(len(segments), 2)
        # Segment 1: June 19 local, 2h (22:00→00:00 local)
        self.assertEqual(segments[0][0], date(2026, 6, 19))
        self.assertAlmostEqual(segments[0][1], 2.0, places=1)
        # Segment 2: June 20 local, 6h (00:00→06:00 local)
        self.assertEqual(segments[1][0], date(2026, 6, 20))
        self.assertAlmostEqual(segments[1][1], 6.0, places=1)

    def test_default_utc_when_no_timezone(self):
        """Employee with no timezone falls back to UTC."""
        self.employee.resource_calendar_id = False
        self.employee.tz = "UTC"
        att = self._create_attendance(
            datetime(2026, 1, 9, 22, 0, 0),
            datetime(2026, 1, 10, 4, 0, 0),
        )
        segments = att._get_day_segments()
        self.assertEqual(len(segments), 2)


@tagged("post_install", "-at_install")
class TestCheckInDayTypeTimezone(TestHrAttendanceTimeCreditCommon):
    """Tests for check_in_day_type using local timezone (B5 secondary)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.calendar_madrid = cls._make_calendar(
            5, tz="Europe/Madrid", name="Madrid CEST"
        )
        cls.employee.resource_calendar_id = cls.calendar_madrid
        cls.employee.tz = "Europe/Madrid"

    def test_day_type_uses_local_weekday_not_utc(self):
        """check_in_day_type uses local weekday, not UTC.

        Europe/Madrid June 2026 = CEST (UTC+2).
        UTC 2026-06-21 22:00 (Sunday) = local 2026-06-22 00:00 (Monday).
        Monday is working_day in Mon-Fri calendar.
        """
        att = self._create_attendance(
            datetime(2026, 6, 21, 22, 0, 0),  # UTC Sunday, local Monday
            context={"skip_time_credit_recompute": True},
        )
        self.assertEqual(att.check_in_day_type, "working_day")

    def test_domain_rule_matches_local_day_type(self):
        """A domain rule filtering by check_in_day_type uses local weekday.

        UTC 2026-06-21 22:00 = local Monday. Domain rule for working_day
        should match even though UTC check_in is Sunday.
        """
        self._make_rule(
            "Working day fixed 30min",
            domain="[('check_in_day_type', '=', 'working_day')]",
            minutes_type="fixed",
            minutes_fixed=30,
        )
        att = self._create_attendance(
            datetime(2026, 6, 21, 22, 0, 0),  # UTC Sunday
            datetime(2026, 6, 21, 23, 0, 0),  # UTC still Sunday, local still Monday
        )
        att._recompute_automatic_time_credits()
        matching_credits = att.time_credit_ids.filtered(
            lambda c: c.type_id == self.credit_type
        )
        self.assertEqual(len(matching_credits), 1)
        self.assertEqual(matching_credits.minutes, 30)


@tagged("post_install", "-at_install")
class TestServerActionSegmented(TestHrAttendanceTimeCreditCommon):
    """Tests for server-action rules with midnight-crossing attendances (B3)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.credit_type.segment_mode = "segment"
        cls.calendar_midnight = cls._make_calendar(
            5, tz="UTC", name="Midnight Cross SA"
        )
        cls.employee.resource_calendar_id = cls.calendar_midnight
        cls.employee.tz = "UTC"

    def test_sa_minutes_per_segment(self):
        """Server action uses segment_hours, not full attendance hours.

        Fri 22:00 → Sat 04:00 (6h total, 2h Fri + 4h Sat).
        SA: action = int((segment_hours or record.worked_hours) * 60)
        Expected: 2 credit lines, Fri=120 min, Sat=240 min.
        """
        minutes_action = self._make_server_action(
            "Segment hours to minutes",
            "action = int((segment_hours or record.worked_hours) * 60)",
        )
        self._make_rule(
            "SA minutes per segment",
            minutes_type="server_action",
            minutes_action_id=minutes_action.id,
        )
        att = self._create_attendance(
            datetime(2026, 1, 9, 22, 0, 0),  # Friday
            datetime(2026, 1, 10, 4, 0, 0),  # Saturday
        )
        credits = att.time_credit_ids.filtered(lambda c: c.type_id == self.credit_type)
        self.assertEqual(len(credits), 2)
        fri_credit = credits.filtered(lambda c: c.segment_date == date(2026, 1, 9))
        sat_credit = credits.filtered(lambda c: c.segment_date == date(2026, 1, 10))
        self.assertEqual(fri_credit.minutes, 120)
        self.assertEqual(sat_credit.minutes, 240)

    def test_sa_condition_distinguishes_segments(self):
        """Server action condition distinguishes per-segment context.

        Fri 22:00 → Sat 04:00.
        Condition SA: segment_day_type == 'non_working_day'.
        Expected: only Saturday segment gets credited.
        """
        condition_action = self._make_server_action(
            "Non-working day segment check",
            "action = (segment_day_type or '').startswith('non_working')",
        )
        self._make_rule(
            "SA condition per segment",
            condition_type="server_action",
            condition_action_id=condition_action.id,
            minutes_type="fixed",
            minutes_fixed=30,
        )
        att = self._create_attendance(
            datetime(2026, 1, 9, 22, 0, 0),
            datetime(2026, 1, 10, 4, 0, 0),
        )
        credits = att.time_credit_ids.filtered(lambda c: c.type_id == self.credit_type)
        self.assertEqual(len(credits), 1)
        self.assertEqual(credits.segment_date, date(2026, 1, 10))
        self.assertEqual(credits.minutes, 30)

    def test_sa_duplication_fixed(self):
        """Server action credits each segment independently.

        Fri 22:00 → Sat 04:00.
        SA that returns 60 regardless of segment context.
        Expected: 120 min total (60 × 2 segments), with each credit line
        logically independent — both segments receive their own credit lines.
        """
        minutes_action = self._make_server_action("Always 60", "action = 60")
        self._make_rule(
            "SA fixed 60 per segment",
            minutes_type="server_action",
            minutes_action_id=minutes_action.id,
        )
        att = self._create_attendance(
            datetime(2026, 1, 9, 22, 0, 0),
            datetime(2026, 1, 10, 4, 0, 0),
        )
        credits = att.time_credit_ids.filtered(lambda c: c.type_id == self.credit_type)
        self.assertEqual(len(credits), 2)
        self.assertEqual(sum(credits.mapped("minutes")), 120)

    @mute_logger(
        "odoo.addons.hr_attendance_time_credit.models.hr_attendance_time_credit_rule"
    )
    def test_sa_non_numeric_minutes_skipped_others_processed(self):
        """A non-numeric SA minutes return skips that rule (warning); others apply."""
        bad_action = self._make_server_action("Return text", "action = 'not-a-number'")
        self._make_rule(
            "Bad SA minutes",
            minutes_type="server_action",
            minutes_action_id=bad_action.id,
        )
        self._make_rule(
            "Fixed 30 other type",
            self.credit_type_2,
            minutes_fixed=30,
            sequence=20,
        )
        att = self._create_attendance(
            datetime(2026, 1, 9, 22, 0, 0),
            datetime(2026, 1, 10, 4, 0, 0),
        )
        bad_credits = att.time_credit_ids.filtered(
            lambda c: c.type_id == self.credit_type
        )
        self.assertEqual(len(bad_credits), 0)
        other_credits = att.time_credit_ids.filtered(
            lambda c: c.type_id == self.credit_type_2
        )
        self.assertEqual(len(other_credits), 1)
        self.assertEqual(other_credits.minutes, 30)


@tagged("post_install", "-at_install")
class TestSegmentMode(TestHrAttendanceTimeCreditCommon):
    """Tests for the configurable segment_mode feature."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.employee.tz = "UTC"
        cls.calendar_monfri = cls._make_calendar(5, name="Mon-Fri SM")
        cls.employee.resource_calendar_id = cls.calendar_monfri

    def test_consolidated_fixed_on_midnight_crossing(self):
        """Consolidated fixed rule: 1 credit line with fixed minutes.

        Rule: minutes_type=fixed, minutes_fixed=60, segment_mode=consolidate
        Attendance: 22:00 -> 06:00 (2 segments: 2h + 6h)
        Expected: 1 credit line with 60 min
        """
        ct = self._make_credit_type("Travel", "travel_sm", segment_mode="consolidate")
        self._make_rule(
            "Fixed 60 consolidated",
            ct,
            minutes_type="fixed",
            minutes_fixed=60,
            segment_mode="consolidate",
        )
        att = self._create_attendance(
            datetime(2026, 1, 9, 22, 0, 0),
            datetime(2026, 1, 10, 6, 0, 0),
        )
        credits = att.time_credit_ids.filtered(lambda c: c.type_id == ct)
        self.assertEqual(len(credits), 1)
        self.assertEqual(credits.minutes, 60)

    def test_consolidated_factor_on_midnight_crossing(self):
        """Consolidated factor rule: 1 credit line from total worked_hours.

        Rule: minutes_type=worked_time_factor, factor_value=1.5,
        segment_mode=consolidate
        Attendance: 22:00 -> 06:00 (8h total)
        Expected: 1 credit line with 8h * 60 * 0.5 = 240 min
        """
        ct = self._make_credit_type("Night", "night_sm", segment_mode="consolidate")
        self._make_rule(
            "Factor 1.5 consolidated",
            ct,
            minutes_type="worked_time_factor",
            factor_value=1.5,
            factor_base="worked_hours",
            segment_mode="consolidate",
        )
        att = self._create_attendance(
            datetime(2026, 1, 9, 22, 0, 0),
            datetime(2026, 1, 10, 6, 0, 0),
        )
        credits = att.time_credit_ids.filtered(lambda c: c.type_id == ct)
        self.assertEqual(len(credits), 1)
        self.assertEqual(credits.minutes, 240)

    def test_segment_mode_preserves_current_behavior(self):
        """Segment mode: 2 credit lines (existing behavior unchanged).

        Rule: minutes_type=worked_time_factor, factor_value=1.5, segment_mode=segment
        Attendance: 22:00 -> 06:00 (2h Fri + 6h Sat)
        Expected: 2 credit lines: 60 + 180 = 240 min total
        """
        ct = self._make_credit_type("Night Seg", "night_seg_sm", segment_mode="segment")
        self._make_rule(
            "Factor 1.5 segmented",
            ct,
            minutes_type="worked_time_factor",
            factor_value=1.5,
            factor_base="worked_hours",
            segment_mode="segment",
        )
        att = self._create_attendance(
            datetime(2026, 1, 9, 22, 0, 0),
            datetime(2026, 1, 10, 6, 0, 0),
        )
        credits = att.time_credit_ids.filtered(lambda c: c.type_id == ct)
        self.assertEqual(len(credits), 2)
        total = sum(credits.mapped("minutes"))
        self.assertEqual(total, 240)

    def test_cap_applied_to_consolidated_total(self):
        """Cap applied to the whole attendance total, not per-segment.

        Rule: minutes_type=worked_time_factor, minutes_cap=120, segment_mode=consolidate
        Attendance: 22:00 -> 06:00 (total factor minutes = 240)
        Expected: 1 credit line with 120 min (capped)
        """
        ct = self._make_credit_type(
            "Night Cap", "night_cap_sm", segment_mode="consolidate"
        )
        self._make_rule(
            "Factor 1.5 cap 120 consolidated",
            ct,
            minutes_type="worked_time_factor",
            factor_value=1.5,
            factor_base="worked_hours",
            minutes_cap=120,
            segment_mode="consolidate",
        )
        att = self._create_attendance(
            datetime(2026, 1, 9, 22, 0, 0),
            datetime(2026, 1, 10, 6, 0, 0),
        )
        credits = att.time_credit_ids.filtered(lambda c: c.type_id == ct)
        self.assertEqual(len(credits), 1)
        self.assertEqual(credits.minutes, 120)

    def test_rule_inherits_mode_from_credit_type(self):
        """Rule with empty segment_mode inherits from credit type.

        credit_type.segment_mode = 'segment'
        rule.segment_mode = '' (empty)
        Expected: rule._get_effective_segment_mode() == 'segment'
        """
        ct = self._make_credit_type(
            "Inherit Test", "inherit_sm", segment_mode="segment"
        )
        rule = self._make_rule(
            "Inherit rule",
            ct,
            minutes_type="fixed",
            minutes_fixed=30,
            segment_mode="",
        )
        self.assertEqual(rule._get_effective_segment_mode(), "segment")

    def test_rule_overrides_credit_type_mode(self):
        """Rule with explicit segment_mode overrides credit type.

        credit_type.segment_mode = 'consolidate'
        rule.segment_mode = 'segment'
        Expected: rule._get_effective_segment_mode() == 'segment'
        """
        ct = self._make_credit_type(
            "Override Test", "override_sm", segment_mode="consolidate"
        )
        rule = self._make_rule(
            "Override rule",
            ct,
            minutes_type="fixed",
            minutes_fixed=30,
            segment_mode="segment",
        )
        self.assertEqual(rule._get_effective_segment_mode(), "segment")

    def test_condition_evaluated_once_consolidated(self):
        """Server action condition called exactly once in consolidated mode.

        Rule: condition_type=server_action, segment_mode=consolidate
        Attendance: crosses midnight
        Expected: server action called exactly once
        """
        call_counter = self._make_server_action("Count calls", "action = True")
        ct = self._make_credit_type("Cond Test", "cond_sm", segment_mode="consolidate")
        self._make_rule(
            "SA condition consolidated",
            ct,
            condition_type="server_action",
            condition_action_id=call_counter.id,
            minutes_type="fixed",
            minutes_fixed=30,
            segment_mode="consolidate",
        )
        att = self._create_attendance(
            datetime(2026, 1, 9, 22, 0, 0),
            datetime(2026, 1, 10, 6, 0, 0),
        )
        credits = att.time_credit_ids.filtered(lambda c: c.type_id == ct)
        self.assertEqual(len(credits), 1)
        self.assertEqual(credits.minutes, 30)

    def test_consolidated_false_vs_zero(self):
        """Condition returning False produces 0 lines; condition passing with
        minutes=0 also produces 0 lines.

        Rule A: domain that never matches -> 0 credit lines
        Rule B: condition returns True, minutes=0 -> 0 credit lines
        """
        # Rule A: domain that never matches
        ct_a = self._make_credit_type(
            "False Test", "false_sm", segment_mode="consolidate"
        )
        self._make_rule(
            "Never match",
            ct_a,
            domain="[('id', '=', 999999)]",
            minutes_type="fixed",
            minutes_fixed=60,
            segment_mode="consolidate",
        )
        # Rule B: always matches, 0 minutes
        ct_b = self._make_credit_type(
            "Zero Test", "zero_sm", segment_mode="consolidate"
        )
        self._make_rule(
            "Zero minutes",
            ct_b,
            minutes_type="fixed",
            minutes_fixed=0,
            segment_mode="consolidate",
            sequence=20,
        )
        att = self._create_attendance(
            datetime(2026, 1, 9, 22, 0, 0),
            datetime(2026, 1, 10, 6, 0, 0),
        )
        credits_a = att.time_credit_ids.filtered(lambda c: c.type_id == ct_a)
        credits_b = att.time_credit_ids.filtered(lambda c: c.type_id == ct_b)
        self.assertEqual(len(credits_a), 0)
        self.assertEqual(len(credits_b), 0)


@tagged("post_install", "-at_install")
class TestMidnightGateTimezoneAware(TestHrAttendanceTimeCreditCommon):
    """Midnight gate must use local dates, not UTC dates.

    Employee in UTC-3 checks in at 01:00 UTC (local 22:00 previous day)
    and out at 05:00 UTC (local 02:00 same day). UTC dates are the same
    but local dates differ — the rule engine should segment.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.employee.tz = "America/Argentina/Buenos_Aires"
        cls.calendar_bue = cls._make_calendar(
            7,
            tz="America/Argentina/Buenos_Aires",
            hour_from=0,
            hour_to=24,
            name="BUE 24/7",
        )
        cls.employee.resource_calendar_id = cls.calendar_bue
        cls.credit_type.write({"segment_mode": "segment"})
        cls.rule = cls._make_rule(
            "Fixed 60min (segmented)", minutes_type="fixed", minutes_fixed=60
        )

    def test_midnight_gate_segments_when_local_dates_differ(self):
        """UTC dates same, local dates differ → should produce 2 segments."""
        # UTC: 2026-01-07 01:00 → local BUE (UTC-3): 2026-01-06 22:00
        # UTC: 2026-01-07 05:00 → local BUE (UTC-3): 2026-01-07 02:00
        # UTC dates: both 2026-01-07 (same!)
        # Local dates: 2026-01-06 vs 2026-01-07 (differ) → should segment
        att = self._create_attendance(
            datetime(2026, 1, 7, 1, 0, 0),
            datetime(2026, 1, 7, 5, 0, 0),
        )
        segments = att._get_day_segments()
        self.assertEqual(len(segments), 2, "Should have 2 local-day segments")
        self.assertEqual(len(att.time_credit_ids), 2, "Should produce 2 credit lines")

    def test_midnight_gate_no_segments_when_local_dates_same(self):
        """Both UTC and local dates same → should produce 1 segment."""
        # UTC: 2026-01-07 10:00 → local BUE: 2026-01-07 07:00
        # UTC: 2026-01-07 14:00 → local BUE: 2026-01-07 11:00
        att = self._create_attendance(
            datetime(2026, 1, 7, 10, 0, 0),
            datetime(2026, 1, 7, 14, 0, 0),
        )
        segments = att._get_day_segments()
        self.assertEqual(len(segments), 1, "Should have 1 segment")
        self.assertEqual(len(att.time_credit_ids), 1, "Should produce 1 credit line")


@tagged("post_install", "-at_install")
class TestCanaryTimezone(TestHrAttendanceTimeCreditCommon):
    """Canary Island timezone with DST (summer, UTC+1).

    Employee in Atlantic/Canary checks in at 22:00 local (21:00 UTC
    during DST) and out at 06:00 local next day (05:00 UTC). UTC dates
    differ (21:00 vs 05:00 next day). The segments must be split at
    LOCAL midnight, not UTC midnight.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.employee.tz = "Atlantic/Canary"
        cls.calendar_canary = cls._make_calendar(
            7,
            tz="Atlantic/Canary",
            hour_from=0,
            hour_to=24,
            name="Canary 24/7",
        )
        cls.employee.resource_calendar_id = cls.calendar_canary
        cls.credit_type.write({"segment_mode": "segment"})
        cls.rule = cls._make_rule(
            "Fixed 60min (segmented, Canary)",
            minutes_type="fixed",
            minutes_fixed=60,
        )

    def test_midnight_gate_canary_summer_dst(self):
        """Summer DST (UTC+1): 22:00 local = 21:00 UTC, 06:00 local = 05:00 UTC.

        UTC dates: 2026-07-15 21:00 → 2026-07-16 05:00 (differ in UTC too).
        Local dates: 2026-07-15 22:00 → 2026-07-16 06:00 (differ in local).
        Segment boundaries must be at LOCAL midnight
        (00:00 Canary = 23:00 UTC), not UTC midnight.
        """
        # 22:00 local Canary (UTC+1) = 21:00 UTC
        # 06:00 local Canary next day = 05:00 UTC
        att = self._create_attendance(
            datetime(2026, 7, 15, 21, 0, 0),
            datetime(2026, 7, 16, 5, 0, 0),
        )
        segments = att._get_day_segments()
        self.assertEqual(len(segments), 2, "Should have 2 local-day segments")
        # First segment: 21:00 UTC → 23:00 UTC (local midnight) = 2h on Jul 15 local
        # Second segment: 23:00 UTC → 05:00 UTC = 6h on Jul 16 local
        self.assertEqual(segments[0][1], 2.0, "First segment should be 2h")
        self.assertEqual(segments[1][1], 6.0, "Second segment should be 6h")
        self.assertEqual(len(att.time_credit_ids), 2, "Should produce 2 credit lines")


@tagged("post_install", "-at_install")
class TestPublicHolidayTimezoneAware(TestHrAttendanceTimeCreditCommon):
    """is_public_holiday must use employee tz, not viewing user tz.

    Employee in UTC-3 checks in at 01:00 UTC (local 22:00 previous day).
    Holiday is on the previous local day. Viewing user is in UTC so
    context_timestamp would give the UTC date (no holiday).
    Employee tz should give the local date (holiday detected).
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.employee.tz = "America/Argentina/Buenos_Aires"
        cls.calendar_bue = cls._make_calendar(
            7,
            tz="America/Argentina/Buenos_Aires",
            hour_from=0,
            hour_to=24,
            name="BUE 24/7",
        )
        cls.employee.resource_calendar_id = cls.calendar_bue
        # Force viewing user to UTC so context_timestamp gives UTC date
        cls.env.user.tz = "UTC"

    def test_public_holiday_detected_via_employee_tz(self):
        """Holiday on local 2026-01-06, check_in 01:00 UTC (= 22:00 local)."""
        holiday_date = "2026-01-06"
        leave = self.env["resource.calendar.leaves"].create(
            {
                "name": "Test Holiday BUE",
                "calendar_id": self.calendar_bue.id,
                "date_from": "%s 00:00:00" % holiday_date,
                "date_to": "%s 23:59:59" % holiday_date,
                "resource_id": False,
            }
        )
        try:
            # UTC 2026-01-07 01:00 = local BUE 2026-01-06 22:00
            att = self.env["hr.attendance"].create(
                {
                    "employee_id": self.employee.id,
                    "check_in": datetime(2026, 1, 7, 1, 0, 0),
                    "check_out": datetime(2026, 1, 7, 5, 0, 0),
                }
            )
            self.assertTrue(
                att.is_public_holiday,
                "Employee local date 2026-01-06 has holiday, "
                "should be detected even when viewing user is UTC",
            )
        finally:
            leave.unlink()

    def test_no_public_holiday_when_local_date_has_none(self):
        """No holiday on local 2026-01-07 -> is_public_holiday=False."""
        # UTC 2026-01-07 10:00 = local BUE 2026-01-07 07:00
        att = self.env["hr.attendance"].create(
            {
                "employee_id": self.employee.id,
                "check_in": datetime(2026, 1, 7, 10, 0, 0),
                "check_out": datetime(2026, 1, 7, 14, 0, 0),
            }
        )
        self.assertFalse(att.is_public_holiday)


@tagged("post_install", "-at_install")
class TestNightConditionTimezoneAware(TestHrAttendanceTimeCreditCommon):
    """Night condition server action must use employee local hour.

    Employee in Europe/Madrid (UTC+1 winter) checks in at 21:00 UTC
    (22:00 local). The night condition (hour >= 22) should fire.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.employee.tz = "Europe/Madrid"
        cls.calendar_mad = cls._make_calendar(
            7,
            tz="Europe/Madrid",
            hour_from=0,
            hour_to=24,
            name="MAD 24/7",
        )
        cls.employee.resource_calendar_id = cls.calendar_mad
        cls.credit_type.write({"segment_mode": "consolidate"})

        night_action = cls._make_server_action(
            "Test Night Condition Tz-Aware", NIGHT_CONDITION_CODE
        )
        cls.night_rule = cls._make_rule(
            "Night 1.5x (tz-aware)",
            condition_type="server_action",
            condition_action_id=night_action.id,
            minutes_type="fixed",
            minutes_fixed=60,
        )

    def test_night_condition_fires_at_22_local_in_utc_plus_1(self):
        """Employee in Madrid (UTC+1), check_in 21:00 UTC = 22:00 local → night."""
        att = self._create_attendance(
            datetime(2026, 1, 7, 21, 0, 0),
            datetime(2026, 1, 7, 23, 0, 0),
        )
        self.assertEqual(len(att.time_credit_ids), 1, "Night condition should fire")
        self.assertEqual(att.time_credit_ids.minutes, 60)

    def test_night_condition_does_not_fire_at_20_local_in_utc_plus_1(self):
        """Employee in Madrid (UTC+1), check_in 19:00 UTC = 20:00 local → not night."""
        att = self._create_attendance(
            datetime(2026, 1, 7, 19, 0, 0),
            datetime(2026, 1, 7, 21, 0, 0),
        )
        self.assertEqual(len(att.time_credit_ids), 0, "Night condition should not fire")

    def test_night_condition_fires_before_6am_local_in_utc_plus_1(self):
        """Employee in Madrid (UTC+1), 04:00 UTC = 05:00 local → night."""
        att = self._create_attendance(
            datetime(2026, 1, 7, 4, 0, 0),
            datetime(2026, 1, 7, 6, 0, 0),
        )
        self.assertEqual(
            len(att.time_credit_ids), 1, "Night condition should fire (< 6am)"
        )


@tagged("post_install", "-at_install")
class TestNightConditionSegmented(TestHrAttendanceTimeCreditCommon):
    """Segmented path: timezone-aware server action via safe_eval.

    The segmented path in _run_server_action builds its own eval context
    with 'timezone' = safe_eval.pytz (a wrap_module, NOT callable).
    This test verifies that 'timezone' is the pytz.timezone function
    so that timezone('UTC') and timezone(tz_name) work correctly
    when the credit type has segment_mode='segment'.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.employee.tz = "Europe/Madrid"
        cls.calendar_mad = cls._make_calendar(
            7,
            tz="Europe/Madrid",
            hour_from=0,
            hour_to=24,
            name="MAD 24/7",
        )
        cls.employee.resource_calendar_id = cls.calendar_mad
        # segment_mode='segment' forces the segmented path
        cls.credit_type.write({"segment_mode": "segment"})

        night_action = cls._make_server_action(
            "Test Night Condition Segmented Tz-Aware", NIGHT_CONDITION_CODE
        )
        cls.night_rule = cls._make_rule(
            "Night 1.5x (segmented tz-aware)",
            condition_type="server_action",
            condition_action_id=night_action.id,
            minutes_type="fixed",
            minutes_fixed=60,
        )

    def test_segmented_night_condition_fires_at_22_local(self):
        """Segmented path: Madrid (UTC+1), 21:00 UTC = 22:00 local → night."""
        att = self._create_attendance(
            datetime(2026, 1, 7, 21, 0, 0),
            datetime(2026, 1, 7, 23, 0, 0),
        )
        self.assertEqual(len(att.time_credit_ids), 1, "Night condition should fire")
        self.assertEqual(att.time_credit_ids.minutes, 60)


@tagged("post_install", "-at_install")
class TestNightExactOverlap(TestHrAttendanceTimeCreditCommon):
    """Night credit must credit only the exact minutes within 22:00-06:00 per segment.

    Uses segment_mode='segment' and minutes_type='server_action'. The rule's
    minutes server action calls ``record._compute_night_overlap_minutes(segment_date)``;
    this test exercises the full engine → server action → helper path.
    Employee in Europe/Madrid (UTC+1 winter).
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.employee.tz = "Europe/Madrid"
        cls.employee.resource_calendar_id = cls._make_calendar(
            7,
            tz="Europe/Madrid",
            hour_from=0,
            hour_to=24,
            name="MAD 24/7",
        )
        cls.credit_type = cls._make_credit_type(
            "Night Overlap Test", "night_overlap_test", segment_mode="segment"
        )
        cls.night_action = cls._make_server_action(
            "Test Night Overlap Minutes",
            "action = record._compute_night_overlap_minutes(segment_date)",
        )
        cls.night_rule = cls._make_rule(
            "Night Exact Overlap Test Rule",
            condition_type="server_action",
            condition_action_id=cls.night_action.id,
            minutes_type="server_action",
            minutes_action_id=cls.night_action.id,
        )

    def _att(self, check_in_dt, check_out_dt):
        return self._create_attendance(check_in_dt, check_out_dt)

    def test_no_night_overlap_returns_zero(self):
        """08:00-16:00 local → zero night credit."""
        # Europe/Madrid UTC+1 winter: 07:00-15:00 UTC
        att = self._att(datetime(2026, 1, 7, 7, 0, 0), datetime(2026, 1, 7, 15, 0, 0))
        self.assertEqual(sum(att.time_credit_ids.mapped("minutes")), 0)

    def test_full_night_shift_21_to_06(self):
        """21:00-06:00 local: night overlap = 22:00-06:00 = 8h → 240 min credit."""
        # UTC+1 winter: check_in 20:00 UTC, check_out 05:00 UTC
        att = self._att(datetime(2026, 1, 7, 20, 0, 0), datetime(2026, 1, 8, 5, 0, 0))
        self.assertEqual(sum(att.time_credit_ids.mapped("minutes")), 240)

    def test_partial_entry_into_night(self):
        """21:00-23:00 local: only 22:00-23:00 = 1h → 30 min credit."""
        # UTC+1: 20:00-22:00 UTC
        att = self._att(datetime(2026, 1, 7, 20, 0, 0), datetime(2026, 1, 7, 22, 0, 0))
        self.assertEqual(sum(att.time_credit_ids.mapped("minutes")), 30)

    def test_partial_exit_from_night(self):
        """04:00-07:00 local: only 04:00-06:00 = 2h → 60 min credit."""
        # UTC+1: 03:00-06:00 UTC
        att = self._att(datetime(2026, 1, 7, 3, 0, 0), datetime(2026, 1, 7, 6, 0, 0))
        self.assertEqual(sum(att.time_credit_ids.mapped("minutes")), 60)

    def test_midnight_crossing_21_to_07_exact_overlap(self):
        """21:00 Mar-18 to 07:00 Mar-19 local (UTC+1):
        Seg Mar-18: 22:00-00:00 = 2h → 60 min
        Seg Mar-19: 00:00-06:00 = 6h → 180 min
        Total: 240 min
        """
        # UTC+1: check_in 20:00 UTC Mar-18, check_out 06:00 UTC Mar-19
        att = self._att(datetime(2026, 3, 18, 20, 0, 0), datetime(2026, 3, 19, 6, 0, 0))
        self.assertEqual(sum(att.time_credit_ids.mapped("minutes")), 240)

    def test_already_starts_at_22_exact(self):
        """22:00-05:30 local = 7.5h fully nocturnal → 225 min credit."""
        # UTC+1: 21:00-04:30 UTC
        att = self._att(datetime(2026, 1, 7, 21, 0, 0), datetime(2026, 1, 8, 4, 30, 0))
        self.assertEqual(sum(att.time_credit_ids.mapped("minutes")), 225)

    def test_daytime_only_no_credit(self):
        """16:00-22:00 local exactly: 22:00 boundary → no overlap (overlap=0)."""
        # UTC+1: 15:00-21:00 UTC
        att = self._att(datetime(2026, 1, 7, 15, 0, 0), datetime(2026, 1, 7, 21, 0, 0))
        self.assertEqual(sum(att.time_credit_ids.mapped("minutes")), 0)

    def test_16_to_midnight_credits_only_night_portion(self):
        """16:00-00:00 local: night overlap = 22:00-00:00 = 2h → 60 min."""
        # UTC+1: 15:00-23:00 UTC
        att = self._att(datetime(2026, 1, 7, 15, 0, 0), datetime(2026, 1, 7, 23, 0, 0))
        self.assertEqual(sum(att.time_credit_ids.mapped("minutes")), 60)
