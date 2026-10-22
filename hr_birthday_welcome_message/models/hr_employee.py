# Copyright 2022 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HrEmployeeBase(models.AbstractModel):
    _inherit = "hr.employee"

    def _attendance_action_change(self, geo_information=None):
        attendance = super()._attendance_action_change(geo_information=geo_information)
        today = fields.Datetime.context_timestamp(self, fields.Datetime.now())
        # We want to take the real employee in case we are using public employee,
        # We are not adding the field directly in order to avoid
        # adding it to public employee
        birthday = self.env["hr.employee"].sudo().browse(self.id).birthday
        # Always return a dict with action info to match _attendance_action format
        result = {
            "action": {},
            "attendance": attendance,
        }
        if birthday and birthday.month == today.month and birthday.day == today.day:
            result["action"]["is_birthday"] = True
        return result
