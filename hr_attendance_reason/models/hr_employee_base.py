# Copyright 2023 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class HrEmployeeBase(models.AbstractModel):
    _inherit = "hr.employee.base"

    show_reasons_on_attendance_screen = fields.Boolean(
        related="company_id.show_reasons_on_attendance_screen", store=True
    )
    required_reason_on_attendance_screen = fields.Boolean(
        related="company_id.required_reason_on_attendance_screen", store=True
    )

    def _attendance_action_change(self):
        attendance = super()._attendance_action_change()
        if self.env.context.get("attendance_reason_id"):
            attendance.attendance_reason_ids = [
                (4, self.env.context.get("attendance_reason_id"))
            ]
        return attendance

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        fields = fields or []
        fields += self.env.context.get("extra_fields", [])
        return super().search_read(
            domain=domain, fields=fields, offset=offset, limit=limit, order=order
        )
