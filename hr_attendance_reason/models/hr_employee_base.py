# Copyright 2023 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class HrEmployeeBase(models.AbstractModel):
    _inherit = "hr.employee.base"

    show_reason_on_attendance_screen = fields.Boolean(
        related="company_id.show_reason_on_attendance_screen", store=True
    )
    required_reason_on_attendance_screen = fields.Boolean(
        related="company_id.required_reason_on_attendance_screen", store=True
    )

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        fields = fields or []
        fields += self.env.context.get("extra_fields", [])
        return super().search_read(
            domain=domain, fields=fields, offset=offset, limit=limit, order=order
        )
