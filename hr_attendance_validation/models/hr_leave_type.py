# Copyright 2025 Pierre Verkest
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import _, api, models
from odoo.tools import format_duration


class HRLeaveType(models.Model):
    _inherit = "hr.leave.type"

    @api.depends("overtime_deductible", "requires_allocation")
    @api.depends_context(
        "request_type", "leave", "holiday_status_display_name", "employee_id"
    )
    def _compute_display_name(self):
        # Exclude hours available in allocation contexts,
        # it might be confusing otherwise
        if (
            not self.requested_display_name()
            or self._context.get("request_type", "leave") == "allocation"
        ):
            return super()._compute_display_name()

        employee = (
            self.env["hr.employee"].browse(self._context.get("employee_id")).sudo()
        )
        overtime_leaves = self.env["hr.leave.type"]
        if employee.total_overtime <= 0:
            overtime_leaves = self.filtered(
                lambda l_type: l_type.overtime_deductible
                and l_type.requires_allocation == "no"
            )
            for leave_type in overtime_leaves:
                leave_type.display_name = "{name} ({count})".format(
                    **{
                        "name": leave_type.name,
                        "count": _(
                            "%s credit hours",
                            format_duration(-1 * employee.total_overtime),
                        ),
                    }
                )
        super(HRLeaveType, self - overtime_leaves)._compute_display_name()
