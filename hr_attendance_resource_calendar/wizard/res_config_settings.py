# Copyright 2025 Binhex <https://www.binhex.cloud>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    restriction_working_schdules = fields.Boolean(
        config_parameter="hr_attendance_resource_calendar.restriction_working_schdules",
        default=False,
    )
