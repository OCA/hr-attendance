# Copyright 2021 Pierre Verkest
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import fields, models


class HrLeave(models.Model):
    _inherit = "hr.leave"

    validation_sheet_id = fields.Many2one(
        "hr.attendance.validation.sheet",
        string="Validation sheet",
    )
