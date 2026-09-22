# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from datetime import datetime

from odoo.tests.common import tagged

from .common import TestHrAttendanceTimeCreditCommon


@tagged("post_install", "-at_install")
class TestProcessCredits(TestHrAttendanceTimeCreditCommon):
    """Tests for the reactive time credit processing pipeline."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.rule_1 = cls._make_rule("Rule 1 - 20min", minutes_fixed=20, sequence=10)
        cls.rule_2 = cls._make_rule(
            "Rule 2 - 10min", cls.credit_type_2, minutes_fixed=10, sequence=20
        )

    def test_process_creates_credit_lines(self):
        """Creating an attendance with check_out should produce credit lines."""
        att = self._create_fixed_attendance(hours=8, check_in_hour=8)
        self.assertEqual(len(att.time_credit_ids), 2)
        minutes_list = att.time_credit_ids.sorted("id").mapped("minutes")
        self.assertEqual(minutes_list, [20, 10])
        rule_by_minutes = {line.minutes: line.rule_id for line in att.time_credit_ids}
        self.assertEqual(rule_by_minutes[20], self.rule_1)
        self.assertEqual(rule_by_minutes[10], self.rule_2)

    def test_reprocess_on_checkout_update(self):
        """Updating check_out should replace automatic lines."""
        att = self._create_attendance(
            datetime(2026, 1, 7, 8, 0, 0),
            datetime(2026, 1, 7, 16, 0, 0),
        )
        self.assertEqual(len(att.time_credit_ids), 2)
        old_ids = att.time_credit_ids.ids
        att.write({"check_out": datetime(2026, 1, 7, 17, 0, 0)})
        self.assertEqual(len(att.time_credit_ids), 2)
        self.assertNotEqual(att.time_credit_ids.ids, old_ids)

    def test_manual_credit_preserved_on_reprocess(self):
        """Manual credit lines should survive when check_out is updated."""
        att = self._create_attendance(
            datetime(2026, 1, 7, 8, 0, 0),
            datetime(2026, 1, 7, 16, 0, 0),
        )
        manual = self.env["hr.attendance.time.credit"].create(
            {
                "attendance_id": att.id,
                "type_id": self.credit_type.id,
                "minutes": 15,
                "origin": "manual",
            }
        )
        self.assertFalse(manual.rule_id)
        att.write({"check_out": datetime(2026, 1, 7, 17, 0, 0)})
        origins = att.time_credit_ids.mapped("origin")
        self.assertIn("manual", origins)
        self.assertIn("automatic", origins)
        # 2 automatic + 1 manual
        self.assertEqual(len(att.time_credit_ids), 3)

    def test_skip_time_credit_not_processed(self):
        """Attendance with skip_time_credit=True should not get automatic credits."""
        att = self._create_fixed_attendance(
            hours=8, check_in_hour=8, skip_time_credit=True
        )
        self.assertEqual(len(att.time_credit_ids), 0)

    def test_skip_time_credit_removes_existing_automatic_lines(self):
        """Setting skip_time_credit=True should clear existing automatic lines."""
        att = self._create_fixed_attendance(hours=8, check_in_hour=8)
        self.assertEqual(len(att.time_credit_ids), 2)
        att.write({"skip_time_credit": True})
        self.assertEqual(
            len(att.time_credit_ids.filtered(lambda line: line.origin == "automatic")),
            0,
        )

    def test_checkout_added_triggers_processing(self):
        """Writing check_out on a previously open attendance triggers processing."""
        att = self._create_attendance(datetime(2026, 1, 7, 8, 0, 0))
        self.assertEqual(len(att.time_credit_ids), 0)
        att.write({"check_out": datetime(2026, 1, 7, 16, 0, 0)})
        self.assertEqual(len(att.time_credit_ids), 2)

    def test_rule_company_filter(self):
        """Rules from a different company should not apply."""
        company_2 = self.env["res.company"].create({"name": "Other Co"})
        self.rule_1.with_context(skip_time_credit_recompute=True).write(
            {"company_id": company_2.id}
        )
        att = self._create_fixed_attendance(hours=8, check_in_hour=8)
        # Only rule_2 matches (same company)
        self.assertEqual(len(att.time_credit_ids), 1)
        self.assertEqual(att.time_credit_ids.type_id, self.credit_type_2)

    def test_rule_unlink_recomputes_without_orphans(self):
        """Deleting a rule should recompute credits and leave no stale rule links."""
        att = self._create_fixed_attendance(hours=8, check_in_hour=8)
        self.assertEqual(len(att.time_credit_ids), 2)
        self.rule_2.unlink()
        att.invalidate_recordset(["time_credit_ids"])
        self.assertEqual(len(att.time_credit_ids), 1)
        self.assertEqual(att.time_credit_ids.rule_id, self.rule_1)
        self.assertEqual(att.time_credit_ids.minutes, 20)

    def test_sequence_ordering(self):
        """Rules should be evaluated and lines created in sequence order."""
        self.rule_1.with_context(skip_time_credit_recompute=True).write(
            {"sequence": 20}
        )
        self.rule_2.with_context(skip_time_credit_recompute=True).write(
            {"sequence": 10}
        )
        att = self._create_fixed_attendance(hours=8, check_in_hour=8)
        types = att.time_credit_ids.sorted("id").mapped("type_id")
        # rule_2 (seq 10) is evaluated first, so its line is created first
        self.assertEqual(types[0], self.credit_type_2)
        self.assertEqual(types[1], self.credit_type)

    def test_locked_skips_recompute_on_write(self):
        """Writing check_out on a locked attendance should not recompute credits."""
        att = self._create_attendance(
            datetime(2026, 1, 7, 8, 0, 0),
            datetime(2026, 1, 7, 16, 0, 0),
        )
        self.assertEqual(len(att.time_credit_ids), 2)
        att.write({"credit_locked": True})
        old_ids = set(att.time_credit_ids.ids)
        att.write({"check_out": datetime(2026, 1, 7, 17, 0, 0)})
        self.assertEqual(set(att.time_credit_ids.ids), old_ids)

    def test_locked_preserves_lines_on_force_reprocess(self):
        """action_process_time_credits should not touch locked records."""
        att = self._create_fixed_attendance(hours=8, check_in_hour=8)
        att.write({"credit_locked": True})
        # Manually remove lines to simulate stale state
        att.time_credit_ids.unlink()
        att.action_process_time_credits()
        self.assertEqual(len(att.time_credit_ids), 0)

    # -- Computed field tests --

    def test_total_credited_hours_with_credits(self):
        """total_credited_hours should include credit minutes."""
        att = self._create_fixed_attendance(hours=8, check_in_hour=8)
        self.env["hr.attendance.time.credit"].create(
            {
                "attendance_id": att.id,
                "type_id": self.credit_type.id,
                "minutes": 60,
                "origin": "manual",
            }
        )
        att.invalidate_recordset(["total_credited_hours"])
        # 2 automatic lines (20+10 min) + 1 manual (60 min) = 90 min = 1.5h
        expected = (att.worked_hours or 0.0) + 1.5
        self.assertAlmostEqual(att.total_credited_hours, expected, places=2)
