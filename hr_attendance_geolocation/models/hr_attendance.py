# Copyright 2019 ForgeFlow S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    check_in_latitude = fields.Float(digits="Location", readonly=True)
    check_in_latitude_text = fields.Char(
        "Check-in Latitude", compute="_compute_check_in_latitude_text"
    )
    check_in_longitude = fields.Float(digits="Location", readonly=True)
    check_in_longitude_text = fields.Char(
        "Check-in Longitude", compute="_compute_check_in_longitude_text"
    )
    check_out_latitude = fields.Float(digits="Location", readonly=True)
    check_out_latitude_text = fields.Char(
        "Check-out Latitude", compute="_compute_check_out_latitude_text"
    )
    check_out_longitude = fields.Float(digits="Location", readonly=True)
    check_out_longitude_text = fields.Char(
        "Check-out Longitude", compute="_compute_check_out_longitude_text"
    )

    def _get_raw_value_from_geolocation(self, dd):
        d = int(dd)
        m = int((dd - d) * 60)
        s = (dd - d - m / 60) * 3600.00
        z = round(s, 2)
        return "%s %sº %s' %s'" % ("N" if d >= 0 else "S", abs(d), abs(m), abs(z))

    @api.depends("check_in_latitude")
    def _compute_check_in_latitude_text(self):
        for item in self:
            item.check_in_latitude_text = (
                self._get_raw_value_from_geolocation(item.check_in_latitude)
                if item.check_in_latitude
                else False
            )

    @api.depends("check_in_longitude")
    def _compute_check_in_longitude_text(self):
        for item in self:
            item.check_in_longitude_text = (
                self._get_raw_value_from_geolocation(item.check_in_longitude)
                if item.check_in_longitude
                else False
            )

    @api.depends("check_out_latitude")
    def _compute_check_out_latitude_text(self):
        for item in self:
            item.check_out_latitude_text = (
                self._get_raw_value_from_geolocation(item.check_out_latitude)
                if item.check_out_latitude
                else False
            )

    @api.depends("check_out_longitude")
    def _compute_check_out_longitude_text(self):
        for item in self:
            item.check_out_longitude_text = (
                self._get_raw_value_from_geolocation(item.check_out_longitude)
                if item.check_out_longitude
                else False
            )
