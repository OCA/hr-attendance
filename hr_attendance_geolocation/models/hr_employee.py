# Copyright 2019 ForgeFlow S.L.
# Copyright 2023 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def _attendance_action_change(self):
        res = super()._attendance_action_change()
        latitude = self.env.context.get("latitude", False)
        longitude = self.env.context.get("longitude", False)
        if latitude and longitude:
            if self.attendance_state == "checked_in":
                res.write(
                    {
                        "check_in_latitude": latitude,
                        "check_in_longitude": longitude,
                    }
                )
            else:
                res.write(
                    {
                        "check_out_latitude": latitude,
                        "check_out_longitude": longitude,
                    }
                )
        return res
