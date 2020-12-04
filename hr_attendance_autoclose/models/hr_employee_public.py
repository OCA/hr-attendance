# Copyright 2020 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HrEmployeePublic(models.Model):

    _inherit = "hr.employee.public"

    no_autoclose = fields.Boolean(string="Don't Autoclose Attendances")
