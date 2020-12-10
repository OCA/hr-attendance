# Copyright 2019 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HrEmployeeBase(models.AbstractModel):
    _inherit = "hr.employee.base"

    no_autoclose = fields.Boolean(string="Don't Autoclose Attendances")
