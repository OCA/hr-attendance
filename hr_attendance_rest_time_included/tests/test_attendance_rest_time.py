# Copyright 2025 Tecnativa - Eduardo Ezerouali
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.tests import tagged

from odoo.addons.base.tests.common import BaseCommon


@tagged("post_install", "-at_install")
class TestHrAttendanceRestTime(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.employee = cls.env["hr.employee"].create(
            {
                "name": "Test Employee",
                "user_id": cls.env.user.id,
            }
        )
        cls.rest_reason = cls.env["hr.attendance.reason"].create(
            {"name": "Rest Time", "rest_time_included": True}
        )

        # Base datetime fixed for test (avoids duplicate overtime)
        cls.base_datetime = "2025-12-22 08:00:00"

    def test_01_create_attendance_and_open_rest_time(self):
        """Test opening and closing a rest time via attendance toggle"""

        # Step 1: Create attendance
        attendance = self.env["hr.attendance"].create(
            {
                "employee_id": self.employee.id,
                "check_in": self.base_datetime,
                "check_out": False,
            }
        )

        # Step 2: Open rest time (with check out)
        self.employee.with_context(
            attendance_reason_id=self.rest_reason.id,
        )._attendance_action_change()

        # Step 3: Check that rest time was created and parent attendance is checked out
        rest_time = self.env["hr.attendance.rest_time"].search(
            [("attendance_id", "=", attendance.id)]
        )
        self.assertEqual(len(rest_time), 1, "Rest time should have been created")
        self.assertTrue(attendance.check_out, "Parent attendance should be checked out")
        self.assertFalse(rest_time.check_out, "Rest time should still be open")

        # Step 4: Close rest time by toggling attendance again
        self.employee._attendance_action_change()

        # Step 5: Verify rest time is closed and parent attendance is reopened
        self.assertTrue(rest_time.check_out, "Rest time should now be closed")
        self.assertFalse(attendance.check_out, "Parent attendance should be reopened")
