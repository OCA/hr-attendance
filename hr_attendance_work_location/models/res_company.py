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
    work_location_mode = fields.Selection(
        [("automatic", "Automatic (GPS)"), ("manual", "Manual (Selector)")],
        default="automatic",
        help="Automatic: work location is resolved from GPS coordinates "
        "at check-in/out. Manual: employee selects work location from a "
        "dropdown in the kiosk/systray.",
    )
    manual_work_location_id = fields.Many2one(
        "hr.work.location",
        string="Default Work Location",
        help="Pre-selected work location in the manual selector. "
        "Leave empty for no default.",
    )
    work_location_required = fields.Boolean(
        default=False,
        help="When enabled, the employee must select a work location "
        "before checking in.",
    )

    _sql_constraints = [
        (
            "geo_tolerance_meters_non_negative",
            "CHECK (geo_tolerance_meters >= 0)",
            "GPS tolerance must be non-negative.",
        ),
    ]
