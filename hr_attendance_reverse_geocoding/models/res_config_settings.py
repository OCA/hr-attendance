# Copyright 2026 Binhex Systems Solutions S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)

PROVIDER_SELECTION = [
    ("mapbox", "Mapbox"),
    # Next providers can be added here
]


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    attendance_geocode_provider = fields.Selection(
        selection=PROVIDER_SELECTION,
        string="Reverse Geocoding Provider",
        default="mapbox",
        config_parameter="hr_attendance_reverse_geocoding.provider",
        help="External provider used for reverse geocoding",
    )
    attendance_geocode_api_key = fields.Char(
        string="Reverse Geocoding API Key",
        config_parameter="hr_attendance_reverse_geocoding.api_key",
        help="API key of the selected geocoding provider",
    )
    attendance_geocode_endpoint = fields.Char(
        string="Reverse Geocoding Endpoint",
        config_parameter="hr_attendance_reverse_geocoding.endpoint",
    )
    geolocation_rounding_precision = fields.Integer(
        config_parameter="hr_attendance_reverse_geocoding.rounding_precision",
    )
