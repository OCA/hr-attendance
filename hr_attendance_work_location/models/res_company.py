# Copyright 2026 Binhex
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    geo_tolerance_meters = fields.Float(
        string="GPS Tolerance (meters)",
        digits=(16, 1),
        default=111.0,
        help="Proximity tolerance in meters for auto-assigning work "
        "locations at check-in/check-out. Default is 111 meters. "
        "Set to 0 to disable automatic matching.",
    )

    _sql_constraints = [
        (
            "geo_tolerance_meters_non_negative",
            "CHECK (geo_tolerance_meters >= 0)",
            "GPS tolerance must be non-negative.",
        ),
    ]
