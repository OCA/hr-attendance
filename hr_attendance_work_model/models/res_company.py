from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    office_ip_address_ids = fields.Many2many(
        comodel_name="res.company.ip.address", string="Offices' IP Addresses"
    )
