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

    def attendance_manual(self, next_action, entered_pin=None):
        res = super().attendance_manual(
            next_action=next_action, entered_pin=entered_pin
        )
        if self.env.context.get("attendance_reason_id"):
            self.last_attendance_id.attendance_reason_ids = [
                (4, self.env.context.get("attendance_reason_id"))
            ]
        return res

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        fields = fields or []
        fields += self.env.context.get("extra_fields", [])
        return super().search_read(
            domain=domain, fields=fields, offset=offset, limit=limit, order=order
        )
