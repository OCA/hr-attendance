# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
"""Midnight segmentation: mode, rate/cap, accumulated base, zones and night overlap."""

from datetime import date, datetime

from odoo.tests.common import tagged
from odoo.tools import mute_logger

from .common import TestHrAttendanceTimeCreditCommon

RULE_LOGGER = (
    "odoo.addons.hr_attendance_time_credit.models.hr_attendance_time_credit_rule"
)


@tagged("post_install", "-at_install")
class TestSegmentationScenario(TestHrAttendanceTimeCreditCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.employee.tz = "UTC"
        cls.employee.resource_calendar_id = cls._make_calendar(
            5, tz="UTC", name="Mon-Fri segmentation"
        )

    @staticmethod
    def _lines(attendance, credit_type):
        return attendance.time_credit_ids.filtered(lambda c: c.type_id == credit_type)

    def test_segment_vs_consolidate_scenario(self):
        type_seg = self._new_type("Segment factor", segment_mode="segment")
        type_rate_seg = self._new_type("Segment rate", segment_mode="segment")
        type_cons = self._new_type("Consolidate factor", segment_mode="consolidate")
        type_rate_cons = self._new_type("Consolidate rate", segment_mode="consolidate")
        self._make_rule(
            "Non-working factor",
            type_seg,
            domain="[('check_in_day_type', '=', 'non_working_day')]",
            minutes_type="worked_time_factor",
            factor_value=2.0,
            sequence=10,
        )
        self._make_rule(
            "Segmented rate and cap",
            type_rate_seg,
            minutes_fixed=60,
            rate=0.5,
            minutes_cap=45,
            sequence=20,
        )
        self._make_rule(
            "Consolidated factor",
            type_cons,
            minutes_type="worked_time_factor",
            factor_value=2.0,
            sequence=30,
        )
        self._make_rule(
            "Consolidated rate and cap",
            type_rate_cons,
            minutes_fixed=60,
            rate=2.0,
            minutes_cap=45,
            sequence=40,
        )

        # Friday 22:00 -> Saturday 04:00: 2h working + 4h non-working.
        att = self._create_attendance(
            datetime(2026, 1, 9, 22, 0), datetime(2026, 1, 10, 4, 0)
        )
        self.assertEqual(
            att._get_day_segments(),
            [(date(2026, 1, 9), 2.0), (date(2026, 1, 10), 4.0)],
        )
        # Segmented: only the Saturday segment satisfies the day-type domain.
        seg_lines = self._lines(att, type_seg)
        self.assertEqual(len(seg_lines), 1)
        self.assertEqual(seg_lines.segment_date, date(2026, 1, 10))
        self.assertAlmostEqual(seg_lines.segment_hours, 4.0)
        self.assertEqual(seg_lines.minutes, 240)  # 4h * 60 * (2 - 1)
        # The cap is consumed across segments: 30 + min(30, 15) = 45.
        rate_seg = self._lines(att, type_rate_seg)
        self.assertEqual(sorted(rate_seg.mapped("minutes")), [15, 30])
        self.assertEqual(sum(rate_seg.mapped("minutes")), 45)
        # Consolidated: one line from the whole 6h attendance, no segment data.
        cons_lines = self._lines(att, type_cons)
        self.assertEqual(len(cons_lines), 1)
        self.assertEqual(cons_lines.minutes, 360)
        self.assertFalse(cons_lines.segment_date)
        # Rate still applies before the cap in consolidated mode.
        self.assertEqual(self._lines(att, type_rate_cons).minutes, 45)

        # Start a clean slate for the accumulated-base part of the scenario.
        for rule in att.time_credit_ids.mapped("rule_id"):
            rule.active = False

        prior_type = self._new_type("Prior fixed", segment_mode="segment")
        accum_type = self._new_type("Accum segment", segment_mode="segment")
        self._make_rule("Prior 60", prior_type, minutes_fixed=60, sequence=5)
        self._make_rule(
            "Accum factor",
            accum_type,
            domain="[('check_in_day_type', '=', 'non_working_day')]",
            minutes_type="worked_time_factor",
            factor_value=2.0,
            factor_base="accumulated_hours",
            sequence=10,
        )
        # Saturday 22:00 -> Sunday 04:00, both non-working days.
        att2 = self._create_attendance(
            datetime(2026, 1, 10, 22, 0), datetime(2026, 1, 11, 4, 0)
        )
        self.assertEqual(
            sorted(self._lines(att2, prior_type).mapped("minutes")), [60, 60]
        )
        accum = self._lines(att2, accum_type)
        minutes_by_day = {line.segment_date: line.minutes for line in accum}
        # Each segment uses its own hours plus only that day's prior credit.
        self.assertEqual(minutes_by_day[date(2026, 1, 10)], 180)  # (2h + 1h) * 60
        self.assertEqual(minutes_by_day[date(2026, 1, 11)], 300)  # (4h + 1h) * 60

    def test_local_timezone_and_night_overlap_scenario(self):
        # Canary Islands observes DST: in July a 22:00 local check-in is 21:00
        # UTC and a 06:00 local check-out is 05:00 UTC the next day.
        canary = self.env["hr.employee"].create(
            {
                "name": "Canary Employee",
                "company_id": self.company.id,
                "tz": "Atlantic/Canary",
                "resource_calendar_id": self._make_calendar(
                    7, tz="Atlantic/Canary", hour_from=0, hour_to=24, name="Canary 24/7"
                ).id,
            }
        )
        canary_type = self._new_type("Canary", segment_mode="segment")
        self._make_rule(
            "Canary fixed",
            canary_type,
            minutes_fixed=60,
            employee_id=canary.id,
        )
        canary_att = self._att_on(canary, date(2026, 7, 15), hours=8, check_in_hour=21)
        self.assertEqual(
            canary_att._get_day_segments(),
            [(date(2026, 7, 15), 2.0), (date(2026, 7, 16), 6.0)],
        )
        self.assertEqual(len(self._lines(canary_att, canary_type)), 2)

        # The night helper is reached through a server action in segmented mode.
        madrid = self.env["hr.employee"].create(
            {
                "name": "Madrid Employee",
                "company_id": self.company.id,
                "tz": "Europe/Madrid",
                "resource_calendar_id": self._make_calendar(
                    7, tz="Europe/Madrid", hour_from=0, hour_to=24, name="Madrid 24/7"
                ).id,
            }
        )
        night_type = self._new_type("Night", segment_mode="segment")
        night_action = self._make_server_action(
            "Night minutes",
            "action = record._compute_night_overlap_minutes(segment_date)",
        )
        self._make_rule(
            "Night overlap",
            night_type,
            condition_type="server_action",
            condition_action_id=night_action.id,
            minutes_type="server_action",
            minutes_action_id=night_action.id,
            employee_id=madrid.id,
        )
        night_att = self._att_on(madrid, date(2026, 1, 7), hours=9, check_in_hour=20)
        self.assertEqual(
            self._lines(night_att, night_type).mapped("minutes"), [60, 180]
        )
        self.assertEqual(night_att._compute_night_overlap_minutes(date(2026, 1, 7)), 60)
        self.assertEqual(
            night_att._compute_night_overlap_minutes(date(2026, 1, 8)), 180
        )

        # A non-numeric minutes return is logged and aborts that rule for the
        # whole segmented attendance, leaving no credit line behind.
        bad_employee = self.env["hr.employee"].create(
            {"name": "Bad SA Employee", "company_id": self.company.id, "tz": "UTC"}
        )
        bad_type = self._new_type("Bad SA", segment_mode="segment")
        bad_action = self._make_server_action("Text minutes", "action = 'oops'")
        self._make_rule(
            "Bad SA rule",
            bad_type,
            minutes_type="server_action",
            minutes_action_id=bad_action.id,
            employee_id=bad_employee.id,
        )
        with mute_logger(RULE_LOGGER):
            bad_att = self._att_on(
                bad_employee, date(2026, 2, 10), hours=8, check_in_hour=20
            )
            self.assertFalse(
                bad_att.time_credit_ids.filtered(lambda c: c.type_id == bad_type)
            )
