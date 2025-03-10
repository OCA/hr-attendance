from odoo import fields, models


class ResCompanyIPAddress(models.Model):
    _name = "res.company.ip.address"
    _description = "Company's IP Addresses"

    name = fields.Char(required=True)
