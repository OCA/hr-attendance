from odoo import fields, models


class IDSecureCompanyMapping(models.Model):
    """Maps iDSecure companies/groups to Odoo companies and employee types."""

    _name = "idsecure.company.mapping"
    _description = "iDSecure Company Mapping"
    _order = "sequence, name"

    sequence = fields.Integer(default=10)
    name = fields.Char(
        string="iDSecure Name",
        required=True,
        help="Name as it appears in ControliD (e.g. 'Gmar', 'MCP', 'RM')",
    )
    idsecure_group_id = fields.Integer(
        string="iDSecure Group ID",
        help="Group ID from ControliD API",
    )
    idsecure_id_type = fields.Selection(
        [("0", "Department"), ("1", "Group"), ("2", "Company")],
        string="Type in ControliD",
        default="2",
    )
    company_id = fields.Many2one(
        "res.company",
        string="Odoo Company",
    )
    employee_type = fields.Selection(
        [("employee", "Employee"), ("freelancer", "Freelancer")],
        default="employee",
        required=True,
    )
    import_attendance = fields.Boolean(
        default=True,
        help="Uncheck to skip (e.g. for visitors/suppliers)",
    )
    device_id = fields.Many2one(
        "idsecure.device",
        string="Device",
        required=True,
        ondelete="cascade",
    )
    active = fields.Boolean(default=True)
