# Copyright 2026 David Palanca Martínez - Grupo Isonor
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from odoo import _, models
from odoo.exceptions import ValidationError


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def _attendance_action_change(self):
        self.ensure_one()
        latitude = self.env.context.get("latitude", None)
        longitude = self.env.context.get("longitude", None)
        if self.company_id.attendance_geolocation_required and (
            not latitude or not longitude
        ):
            raise ValidationError(_("You must activate location and GPS to clock in."))
        return super()._attendance_action_change()
