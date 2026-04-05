# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields
from odoo.tests.common import tagged

from .common import TestHrAttendanceAllowanceCommon


@tagged("post_install", "-at_install")
class TestProcessAttendances(TestHrAttendanceAllowanceCommon):
    """Tests for the reactive allowance processing pipeline."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.rule_1 = cls.env["hr.attendance.allowance.rule"].create(
            {
                "name": "Rule 1 - 20min",
                "allowance_type_id": cls.allowance_type.id,
                "company_id": cls.company.id,
                "condition_type": "domain",
                "domain": "[]",
                "minutes_type": "fixed",
                "minutes_fixed": 20,
                "sequence": 10,
            }
        )
        cls.rule_2 = cls.env["hr.attendance.allowance.rule"].create(
            {
                "name": "Rule 2 - 10min",
                "allowance_type_id": cls.allowance_type_2.id,
                "company_id": cls.company.id,
                "condition_type": "domain",
                "domain": "[]",
                "minutes_type": "fixed",
                "minutes_fixed": 10,
                "sequence": 20,
            }
        )

    def test_process_creates_allowance_lines(self):
        """Creating an attendance with check_out should produce allowance lines."""
        now = fields.Datetime.now()
        att = self._create_attendance(fields.Datetime.subtract(now, hours=8), now)
        self.assertEqual(len(att.allowance_ids), 2)
        minutes_list = att.allowance_ids.sorted("id").mapped("minutes")
        self.assertEqual(minutes_list, [20, 10])

    def test_process_sets_origin_automatic(self):
        """All engine-created allowance lines should have origin=automatic."""
        now = fields.Datetime.now()
        att = self._create_attendance(fields.Datetime.subtract(now, hours=8), now)
        self.assertTrue(all(a.origin == "automatic" for a in att.allowance_ids))

    def test_reprocess_on_checkout_update(self):
        """Updating check_out should replace automatic lines."""
        now = fields.Datetime.now()
        att = self._create_attendance(fields.Datetime.subtract(now, hours=8), now)
        self.assertEqual(len(att.allowance_ids), 2)
        old_ids = att.allowance_ids.ids
        att.write({"check_out": fields.Datetime.add(now, hours=1)})
        self.assertEqual(len(att.allowance_ids), 2)
        self.assertNotEqual(att.allowance_ids.ids, old_ids)

    def test_manual_allowance_preserved_on_reprocess(self):
        """Manual allowance lines should survive when check_out is updated."""
        now = fields.Datetime.now()
        att = self._create_attendance(fields.Datetime.subtract(now, hours=8), now)
        self.env["hr.attendance.allowance"].create(
            {
                "attendance_id": att.id,
                "type_id": self.allowance_type.id,
                "minutes": 15,
                "origin": "manual",
            }
        )
        att.write({"check_out": fields.Datetime.add(now, hours=1)})
        origins = att.allowance_ids.mapped("origin")
        self.assertIn("manual", origins)
        self.assertIn("automatic", origins)
        # 2 automatic + 1 manual
        self.assertEqual(len(att.allowance_ids), 3)

    def test_skip_allowance_not_processed(self):
        """Attendance with skip_allowance=True should not get automatic allowances."""
        now = fields.Datetime.now()
        att = self._create_attendance(
            fields.Datetime.subtract(now, hours=8),
            now,
            skip_allowance=True,
        )
        self.assertEqual(len(att.allowance_ids), 0)

    def test_skip_allowance_removes_existing_automatic_lines(self):
        """Setting skip_allowance=True should clear existing automatic lines."""
        now = fields.Datetime.now()
        att = self._create_attendance(fields.Datetime.subtract(now, hours=8), now)
        self.assertEqual(len(att.allowance_ids), 2)
        att.write({"skip_allowance": True})
        self.assertEqual(
            len(att.allowance_ids.filtered(lambda line: line.origin == "automatic")), 0
        )

    def test_no_checkout_not_processed(self):
        """Attendance without check_out should not get allowance lines."""
        now = fields.Datetime.now()
        att = self._create_attendance(fields.Datetime.subtract(now, hours=8))
        self.assertEqual(len(att.allowance_ids), 0)

    def test_checkout_added_triggers_processing(self):
        """Writing check_out on a previously open attendance triggers processing."""
        now = fields.Datetime.now()
        att = self._create_attendance(fields.Datetime.subtract(now, hours=8))
        self.assertEqual(len(att.allowance_ids), 0)
        att.write({"check_out": now})
        self.assertEqual(len(att.allowance_ids), 2)

    def test_rule_company_filter(self):
        """Rules from a different company should not apply."""
        company_2 = self.env["res.company"].create({"name": "Other Co"})
        self.rule_1.with_context(skip_allowance_recompute=True).write(
            {"company_id": company_2.id}
        )
        now = fields.Datetime.now()
        att = self._create_attendance(fields.Datetime.subtract(now, hours=8), now)
        # Only rule_2 matches (same company)
        self.assertEqual(len(att.allowance_ids), 1)
        self.assertEqual(att.allowance_ids.type_id, self.allowance_type_2)

    def test_sequence_ordering(self):
        """Rules should be evaluated and lines created in sequence order."""
        self.rule_1.with_context(skip_allowance_recompute=True).write({"sequence": 20})
        self.rule_2.with_context(skip_allowance_recompute=True).write({"sequence": 10})
        now = fields.Datetime.now()
        att = self._create_attendance(fields.Datetime.subtract(now, hours=8), now)
        types = att.allowance_ids.sorted("id").mapped("type_id")
        # rule_2 (seq 10) is evaluated first, so its line is created first
        self.assertEqual(types[0], self.allowance_type_2)
        self.assertEqual(types[1], self.allowance_type)

    def test_locked_skips_recompute_on_write(self):
        """Writing check_out on a locked attendance should not recompute allowances."""
        now = fields.Datetime.now()
        att = self._create_attendance(fields.Datetime.subtract(now, hours=8), now)
        self.assertEqual(len(att.allowance_ids), 2)
        att.write({"allowance_locked": True})
        old_ids = set(att.allowance_ids.ids)
        att.write({"check_out": fields.Datetime.add(now, hours=1)})
        self.assertEqual(set(att.allowance_ids.ids), old_ids)

    def test_locked_preserves_lines_on_force_reprocess(self):
        """action_process_allowances should not touch locked records."""
        now = fields.Datetime.now()
        att = self._create_attendance(fields.Datetime.subtract(now, hours=8), now)
        att.write({"allowance_locked": True})
        # Manually remove lines to simulate stale state
        att.allowance_ids.unlink()
        att.action_process_allowances()
        self.assertEqual(len(att.allowance_ids), 0)

    def test_skip_allowance_recompute_context(self):
        """Context flag should suppress allowance recompute."""
        now = fields.Datetime.now()
        att = self._create_attendance(
            fields.Datetime.subtract(now, hours=8),
            now,
            context={"skip_allowance_recompute": True},
        )
        self.assertEqual(len(att.allowance_ids), 0)

    # -- Computed field tests --

    def test_total_credited_hours_with_allowance(self):
        """total_credited_hours should include allowance minutes."""
        now = fields.Datetime.now()
        att = self._create_attendance(fields.Datetime.subtract(now, hours=8), now)
        self.env["hr.attendance.allowance"].create(
            {
                "attendance_id": att.id,
                "type_id": self.allowance_type.id,
                "minutes": 60,
                "origin": "manual",
            }
        )
        att.invalidate_recordset(["total_credited_hours"])
        # 2 automatic lines (20+10 min) + 1 manual (60 min) = 90 min = 1.5h
        expected = (att.worked_hours or 0.0) + 1.5
        self.assertAlmostEqual(att.total_credited_hours, expected, places=2)

    def test_total_credited_hours_no_allowance(self):
        """Without allowances, total_credited_hours equals worked_hours."""
        now = fields.Datetime.now()
        att = self._create_attendance(
            fields.Datetime.subtract(now, hours=8),
            now,
            context={"skip_allowance_recompute": True},
        )
        self.assertAlmostEqual(
            att.total_credited_hours, att.worked_hours or 0.0, places=2
        )
