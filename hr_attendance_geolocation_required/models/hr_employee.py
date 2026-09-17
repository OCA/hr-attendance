# Copyright 2026 David Palanca Martínez - Grupo Isonor
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import _, models
from odoo.exceptions import ValidationError


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def _attendance_action_change(self, geo_information=None):
        self.ensure_one()
        if self.company_id.attendance_geolocation_required and (
            not geo_information
            or not geo_information.get("latitude")
            or not geo_information.get("longitude")
        ):
            raise ValidationError(_("You must activate location and GPS to clock in."))
        return super()._attendance_action_change(geo_information)
