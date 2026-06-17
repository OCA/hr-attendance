# Copyright 2026 Binhex Systems Solutions S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class HrAttendanceGeocodeCache(models.Model):
    _name = "hr.attendance.geocode.cache"
    _description = "HR Attendance Geocode Cache"
    _order = "write_date desc"

    latitude_normalize = fields.Float(string="Latitude", required=True, index=True)
    longtide_normalize = fields.Float(string="Longitude", required=True, index=True)
    address = fields.Char(required=True)
    provider = fields.Char(required=True, index=True)
    map_url = fields.Char(
        string="Map URL",
        help="External link to view the location on a map",
    )
