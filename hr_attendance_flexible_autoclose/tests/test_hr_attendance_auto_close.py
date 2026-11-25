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

        cls.calendar = cls.env["resource.calendar"].create(
            {"name": "40h/week", "hours_per_day": 8.0, "tz": "UTC"}
        )
        cls.employee.resource_calendar_id = cls.calendar
        cls.env.company.auto_check_out = True
        cls.env.company.auto_check_out_tolerance = 0.25

    def test_auto_check_out_with_reason(self):
        check_in = datetime.now() - relativedelta(hours=10)
        att = self.hr_attendance.create(
            {
                "employee_id": self.employee.id,
                "check_in": check_in.strftime(DF),
            }
        )

        self.hr_attendance._cron_auto_check_out()

        self.assertTrue(att.check_out, "Should be auto checked out")

    def test_auto_check_out_without_reason(self):
        check_in = datetime.now() - relativedelta(hours=10)
        att = self.hr_attendance.create(
            {
                "employee_id": self.employee.id,
                "check_in": check_in.strftime(DF),
            }
        )

        self.hr_attendance._cron_auto_check_out()

        self.assertTrue(att.check_out, "Should be auto checked out")

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
