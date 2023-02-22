from odoo import fields, models, api


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    @api.constrains('check_in', 'check_out', 'employee_id')
    def _check_validity(self):
        self.employee_id._attendance_ip_check()
        return super()._check_validity()