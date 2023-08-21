# Copyright 2023 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)


from odoo import _, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    hr_attendance_break_min_break = fields.Float(
        related="company_id.hr_attendance_break_min_break", readonly=False
    )

    def button_hr_attendance_break_thresholds(self):
        return {
            "type": "ir.actions.act_window",
            "name": _("Edit break thresholds"),
            "res_model": "hr.attendance.break.threshold",
            "domain": [("company_id", "=", self.company_id.id)],
            "views": [(False, "tree")],
            "context": {
                "default_company_id": self.company_id.id,
            },
        }

    def button_hr_attendance_break_action(self):
        action = self.env.ref("hr_attendance_break.action_mandatory_break")
        return {
            "type": "ir.actions.act_window",
            "name": action.name,
            "res_model": action._name,
            "res_id": action.id,
            "views": [(False, "form")],
        }
