# Copyright 2026 Binhex
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    geo_tolerance_meters = fields.Float(
        related="company_id.geo_tolerance_meters",
        readonly=False,
    )
    work_location_mode = fields.Selection(
        related="company_id.work_location_mode",
        readonly=False,
    )
    manual_work_location_id = fields.Many2one(
        related="company_id.manual_work_location_id",
        readonly=False,
    )
    work_location_required = fields.Boolean(
        related="company_id.work_location_required",
        readonly=False,
    )
