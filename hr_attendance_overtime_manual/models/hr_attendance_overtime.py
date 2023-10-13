# © 2023 initOS GmbH
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class HrAttendanceOvertime(models.Model):
    _inherit = "hr.attendance.overtime"

    note = fields.Char()
