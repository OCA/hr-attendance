from odoo import api, fields, models


class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    work_model_type = fields.Selection(
        selection=[
            ("office", "Office"),
            ("remote", "Remote"),
        ],
        string="Work Model",
        compute="_compute_work_model_type",
        store=True,
    )

    @api.depends(
        "employee_id.company_id.office_ip_address_ids",
        "in_ip_address",
        "out_ip_address",
    )
    def _compute_work_model_type(self):
        office_ip_address_by_company_dict = {
            company.id: [
                ip_address.name for ip_address in company.office_ip_address_ids
            ]
            for company in self.env["res.company"].search([])
        }
        for attendance in self:
            company_id = attendance.employee_id.company_id.id
            office_ip_addresses = office_ip_address_by_company_dict.get(
                company_id, False
            )
            work_model_type = "office"
            ip_address = attendance.out_ip_address or attendance.in_ip_address
            for office_ip_address in office_ip_addresses:
                if office_ip_address and ip_address and ip_address != office_ip_address:
                    work_model_type = "remote"
                    break
            attendance.work_model_type = work_model_type
