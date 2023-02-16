# Copyright 2023 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class HrEmployeeBase(models.AbstractModel):
    _inherit = "hr.employee.base"

    show_reasons_on_attendance_screen = fields.Boolean(
        related="company_id.show_reasons_on_attendance_screen", store=True
    )
