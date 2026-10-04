import urllib

from odoo import api, fields, models


class HrAttendanceLocation(models.Model):
    _name = "hr.attendance.location"
    _description = "Authorized location for HR attendance"

    name = fields.Char(required=True)
    latitude = fields.Float(required=True, digits=(16, 8))
    longitude = fields.Float(required=True, digits=(16, 8))
    radius_m = fields.Integer(string="Radius (m)", default=150)
    note = fields.Text()
    map_url = fields.Char(string="View on map", compute="_compute_map_url")

    @api.depends("latitude", "longitude", "radius_m")
    def _compute_map_url(self):
        for rec in self:
            if rec.latitude and rec.longitude and rec.radius_m:
                color_fill = "%23AAAAAA"
                color_border = "%23000000"
                opacity = 0.4
                circle_data = (
                    f"[[{rec.radius_m},{rec.latitude},{rec.longitude},"
                    f'"{color_fill}","{color_border}",{opacity}]]'
                )
                encoded = urllib.parse.quote(circle_data, safe="")
                rec.map_url = f"https://www.mapdevelopers.com/draw-circle-tool.php?circles={encoded}"
            else:
                rec.map_url = False

    @api.constrains("radius_m")
    def _check_radius(self):
        for rec in self:
            if rec.radius_m <= 0:
                raise models.ValidationError_("Radius must be > 0")
