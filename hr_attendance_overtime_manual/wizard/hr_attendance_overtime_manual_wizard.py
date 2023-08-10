# © 2023 initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, fields, models


class TimesheetWizard(models.TransientModel):
    _name = "hr.attendance.overtime.wizard"
    _description = _("Wizard to add manual overtime")

    date = fields.Date(
        string="Day", required=True, default=lambda _: fields.Date.today()
    )
    duration = fields.Float(string="Extra Hours", default=1.0, required=True)
    note = fields.Char(required=True)

    def action_create(self):
        self.env["hr.attendance.overtime"].create(
            {
                "employee_id": self.env.context.get("active_id"),
                "date": self.date,
                "duration": self.duration,
                "note": self.note,
                "adjustment": True,
            }
        )
