# Copyright 2022 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HrEmployeeBase(models.AbstractModel):
    _inherit = "hr.employee.base"

    def _attendance_action(self, next_action):
        result = super()._attendance_action(next_action)
        today = fields.Datetime.context_timestamp(self, fields.Datetime.now())
        # We want to take the real employee in case we are using public employee,
        # We are not adding the field directly in order to avoid adding it to public employee
        birthday = self.env["hr.employee"].sudo().browse(self.id).birthday
        if birthday and birthday.month == today.month and birthday.day == today.day:
            result["action"]["is_birthday"] = True
        return result
