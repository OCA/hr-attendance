from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    idsecure_id = fields.Integer(
        string="iDSecure ID",
        index=True,
        copy=False,
        help=(
            "User ID in the iDSecure access control system (idUser). "
            "Used for reliable employee matching. You can find this value "
            "in the iDSecure admin panel under the user's profile."
        ),
    )
    idsecure_log_ids = fields.One2many(
        "idsecure.access.log",
        "employee_id",
        string="Access Events",
    )
    idsecure_log_count = fields.Integer(
        compute="_compute_idsecure_log_count",
        string="Access Events",
    )

    def _compute_idsecure_log_count(self):
        for emp in self:
            emp.idsecure_log_count = self.env["idsecure.access.log"].search_count(
                [("employee_id", "=", emp.id)]
            )

    def init(self):
        """Create partial unique index: idsecure_id must be unique when set (> 0)."""
        self.env.cr.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS hr_employee_idsecure_id_unique
            ON hr_employee (idsecure_id)
            WHERE idsecure_id > 0
        """
        )


class HrEmployeePublic(models.Model):
    """Mirror the field on the public model.

    hr.employee.public is what a regular user reads, so a field that only
    exists on hr.employee raises "Invalid field" as soon as any other module
    reads employee data without HR rights.
    """

    _inherit = "hr.employee.public"

    idsecure_id = fields.Integer(readonly=True)
