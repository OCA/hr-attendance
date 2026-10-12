# Copyright 2025 ForgeFlow S.L. (https://www.forgeflow.com)
# Part of ForgeFlow. See LICENSE file for full copyright and licensing details.


from odoo import fields, models


class HrEmployeeBase(models.AbstractModel):
    _inherit = "hr.employee.base"

    allow_kiosk_access = fields.Boolean(
        default=True,
        help="If enabled, the employee is selectable in the kiosk for attendance "
        "registration.",
    )
