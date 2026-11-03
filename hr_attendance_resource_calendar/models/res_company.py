# Copyright 2025 Binhex <https://www.binhex.cloud>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    restriction_working_schedules = fields.Boolean(
        string="Restrict Attendances to Working Schedules",
        help="Employees of this company can only check in within the periods "
        "of their working schedule.",
    )
