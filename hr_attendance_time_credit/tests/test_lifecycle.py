# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
"""Recompute lifecycle and lookback windows in two connected scenarios."""

from datetime import datetime

from freezegun import freeze_time

from odoo.exceptions import UserError
from odoo.tests.common import tagged

from .common import TestHrAttendanceTimeCreditCommon


@tagged("post_install", "-at_install")
class TestRecomputeLifecycleScenario(TestHrAttendanceTimeCreditCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["ir.config_parameter"].sudo().set_param(
            "hr_attendance_time_credit.cron_lookback_days", "0"
        )
        cls.rule_1 = cls._make_rule("Rule 1", minutes_fixed=20, sequence=10)
        cls.rule_2 = cls._make_rule(
            "Rule 2", cls.credit_type_2, minutes_fixed=10, sequence=20
        )

    def _automatic(self, attendance):
        return attendance.time_credit_ids.filtered(lambda c: c.origin == "automatic")

    def test_recompute_lifecycle_scenario(self):
        att = self._create_fixed_attendance(hours=8, check_in_hour=8)
        self.assertEqual(sorted(self._automatic(att).mapped("minutes")), [10, 20])

        # A manual line is left alone by every recompute.
        manual = self.env["hr.attendance.time.credit"].create(
            {
                "attendance_id": att.id,
                "type_id": self.credit_type.id,
                "minutes": 15,
                "origin": "manual",
            }
        )
        att.write({"check_out": datetime(2026, 1, 7, 17, 0)})
        self.assertEqual(len(att.time_credit_ids), 3)
        self.assertIn(manual, att.time_credit_ids)

        # Skipping clears only the automatic lines; turning it back on
        # regenerates them without disturbing the manual one.
        att.write({"skip_time_credit": True})
        self.assertEqual(att.time_credit_ids, manual)
        att.write({"skip_time_credit": False})
        self.assertEqual(len(att.time_credit_ids), 3)
        self.assertIn(manual, att.time_credit_ids)

        # A lock freezes the engine and refuses manual edits, even as manager.
        att.write({"credit_locked": True})
        old_ids = set(self._automatic(att).ids)
        att.write({"check_out": datetime(2026, 1, 7, 18, 0)})
        att.action_process_time_credits()
        self.assertEqual(set(self._automatic(att).ids), old_ids)
        vals = {
            "attendance_id": att.id,
            "type_id": self.credit_type.id,
            "minutes": 5,
        }
        Credit = self.env["hr.attendance.time.credit"]
        with self.assertRaises(UserError):
            Credit.create(vals)
        with self.assertRaises(UserError):
            att.time_credit_ids[0].write({"minutes": 1})
        with self.assertRaises(UserError):
            att.time_credit_ids[0].unlink()
        att.write({"credit_locked": False})

        # The force action reprocesses a whole selection, ignoring the clock.
        att2 = self._create_attendance(
            datetime(2026, 1, 10, 8, 0),
            datetime(2026, 1, 10, 10, 0),
            context={"skip_time_credit_recompute": True},
        )
        att3 = self._create_attendance(
            datetime(2026, 1, 11, 8, 0),
            datetime(2026, 1, 11, 10, 0),
            context={"skip_time_credit_recompute": True},
        )
        self.assertFalse((att2 | att3).time_credit_ids)
        self.assertTrue((att2 | att3).action_process_time_credits())
        self.assertEqual(len(self._automatic(att2)), 2)
        self.assertEqual(len(self._automatic(att3)), 2)

        # Rule edits cascade; unlinking leaves no stale rule link behind.
        self.rule_1.write({"minutes_fixed": 30})
        att.invalidate_recordset(["time_credit_ids"])
        self.assertIn(30, self._automatic(att).mapped("minutes"))
        self.rule_2.unlink()
        att.invalidate_recordset(["time_credit_ids"])
        self.assertEqual(self._automatic(att).mapped("minutes"), [30])
        self.assertEqual(self._automatic(att).rule_id, self.rule_1)


@tagged("post_install", "-at_install")
class TestLookbackWindowScenario(TestHrAttendanceTimeCreditCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.rule = cls._make_rule("Lookback rule", minutes_fixed=15)
        cls.param = cls.env["ir.config_parameter"].sudo()

    @freeze_time("2026-06-01 12:00:00")
    def test_cron_lookback_scenario(self):
        self.param.set_param("hr_attendance_time_credit.cron_lookback_days", "90")
        recent = self._create_attendance(
            datetime(2026, 5, 20, 8, 0), datetime(2026, 5, 20, 16, 0)
        )
        old = self._create_attendance(
            datetime(2026, 1, 7, 8, 0), datetime(2026, 1, 7, 16, 0)
        )
        self.assertEqual(recent.time_credit_ids.minutes, 15)
        self.assertEqual(old.time_credit_ids.minutes, 15)

        # The cascade is bounded by the same lookback: only the recent row is
        # refreshed when the rule changes.
        self.rule.write({"minutes_fixed": 30})
        recent.invalidate_recordset(["time_credit_ids"])
        old.invalidate_recordset(["time_credit_ids"])
        self.assertEqual(recent.time_credit_ids.minutes, 30)
        self.assertEqual(old.time_credit_ids.minutes, 15)

        recent.time_credit_ids.unlink()
        old.time_credit_ids.unlink()
        self.env["hr.attendance"]._cron_process_time_credits()
        recent.invalidate_recordset(["time_credit_ids"])
        old.invalidate_recordset(["time_credit_ids"])
        self.assertEqual(recent.time_credit_ids.minutes, 30)
        self.assertFalse(old.time_credit_ids)

        # Zero means no cutoff, both for the cron and for the force action.
        self.param.set_param("hr_attendance_time_credit.cron_lookback_days", "0")
        self.assertEqual(self.env["hr.attendance"]._get_time_credit_lookback_days(), 0)
        old.action_process_time_credits()
        self.assertEqual(old.time_credit_ids.minutes, 30)
        old.time_credit_ids.unlink()
        self.env["hr.attendance"]._cron_process_time_credits()
        old.invalidate_recordset(["time_credit_ids"])
        self.assertEqual(old.time_credit_ids.minutes, 30)

        # An absent/empty parameter falls back to 90 days, so the old row is
        # skipped again by the cron but a forced reprocess still updates it.
        self.param.set_param("hr_attendance_time_credit.cron_lookback_days", "")
        self.assertEqual(self.env["hr.attendance"]._get_time_credit_lookback_days(), 90)
        old.time_credit_ids.unlink()
        self.env["hr.attendance"]._cron_process_time_credits()
        old.invalidate_recordset(["time_credit_ids"])
        self.assertFalse(old.time_credit_ids)
        old.action_process_time_credits()
        self.assertEqual(old.time_credit_ids.minutes, 30)
