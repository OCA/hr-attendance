# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo.tests.common import tagged

from odoo.addons.base.tests.common import BaseCommon


@tagged("post_install", "-at_install")
class TestHrAttendanceAllowanceCommon(BaseCommon):
    """Shared setUp for all attendance allowance tests."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.employee = cls.env["hr.employee"].create(
            {"name": "Test Employee", "company_id": cls.company.id}
        )
        cls.allowance_type = cls.env["hr.attendance.allowance.type"].create(
            {
                "name": "Travel Time",
                "code": "travel",
                "company_id": cls.company.id,
            }
        )
        cls.allowance_type_2 = cls.env["hr.attendance.allowance.type"].create(
            {
                "name": "Dressing Time",
                "code": "dressing",
                "company_id": cls.company.id,
            }
        )
        cls.hr_attendance_model_id = cls.env["ir.model"]._get_id("hr.attendance")

    @classmethod
    def _create_attendance(cls, check_in_dt, check_out_dt=None, context=None, **kwargs):
        vals = {
            "employee_id": cls.employee.id,
            "check_in": check_in_dt,
        }
        if check_out_dt:
            vals["check_out"] = check_out_dt
        vals.update(kwargs)
        env = (
            cls.env(context={**cls.env.context, **(context or {})})
            if context
            else cls.env
        )
        return env["hr.attendance"].create(vals)
