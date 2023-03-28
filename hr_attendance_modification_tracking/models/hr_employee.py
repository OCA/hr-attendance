# Copyright 2023 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HrEmployeeBase(models.AbstractModel):
    _inherit = "hr.employee.base"

    last_check_in = fields.Datetime(tracking=False)
    last_check_out = fields.Datetime(tracking=False)

    def _valid_field_parameter(self, field, name):
        return name == "tracking" or super()._valid_field_parameter(field, name)
