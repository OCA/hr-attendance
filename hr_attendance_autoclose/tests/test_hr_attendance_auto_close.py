# Copyright 2018 ForgeFlow, S.L.
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo.tests import new_test_user, users
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DF

from odoo.addons.base.tests.common import BaseCommon


class TestHrAttendanceReason(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.hr_attendance = cls.env["hr.attendance"]
        cls.employee = cls.env["hr.employee"].create({"name": "Employee"})
        new_test_user(cls.env, login="test-user")

    def test_employee_edit(self):
        """Test that incomplete attendances are auto-closed
        after the configured duration."""
        check_in_time = datetime.now()
        check_out_time = datetime.now() + relativedelta(hours=7)
        att = self.hr_attendance.create(
            {
                "employee_id": self.employee.id,
                "check_in": check_in_time.strftime(DF),
                "check_out": check_out_time.strftime(DF),
            }
        )
        self.assertEqual(att.open_worked_hours, 7.0, "Wrong hours")
        past_check_in_time = datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        ) - relativedelta(hours=15)
        att = self.hr_attendance.create(
            {
                "employee_id": self.employee.id,
                "check_in": past_check_in_time.strftime(DF),
            }
        )
        self.hr_attendance.check_for_incomplete_attendances()
        # The auto-close mechanism sets check_out = check_in + max_hours
        # (default 11.0 on the company).
        # So worked_hours equals attendance_maximum_hours_per_day minus the
        # lunch break duration.
        # It should be 10.0 as we should have a lunch break of 1 hour in demo data.
        launch_break = sum(
            self.employee.resource_calendar_id.attendance_ids.filtered(
                lambda resource_attendance: resource_attendance.day_period == "lunch"
            ).mapped("duration_hours")
        )
        expected_hours = (
            self.employee.company_id.attendance_maximum_hours_per_day - launch_break
        )
        self.assertEqual(att.worked_hours, expected_hours, "Attendance not closed")
        reason = self.env.company.hr_attendance_autoclose_reason
        reason.unlink()
        check_in_time += relativedelta(hours=10)
        check_out_time += relativedelta(hours=10)
        att2 = self.hr_attendance.create(
            {
                "employee_id": self.employee.id,
                "check_in": check_in_time.strftime(DF),
                "check_out": check_out_time.strftime(DF),
            }
        )
        self.hr_attendance.check_for_incomplete_attendances()
        self.assertFalse(att2.attendance_reason_ids)

    @users("test-user")
    def test_hr_employee_can_still_read_employee_and_hr_public_employee(self):
        """This test ensure the following comment from hr.employee model has been take
        in consideration::

            NB: Any field only available on the model hr.employee (i.e. not on the
            hr.employee.public model) should have `groups="hr.group_hr_user"` on its
            definition to avoid being prefetched when the user hasn't access to the
            hr.employee model. Indeed, the prefetch loads the data for all the fields
            that are available according to the group defined on them.
        """
        for empl in self.env["hr.employee"].search([]):
            self.assertTrue(empl.name)
