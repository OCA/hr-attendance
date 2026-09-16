from odoo import _, api, fields, models


class IDSecureSyncWizard(models.TransientModel):
    """Wizard to help map unmatched iDSecure users to Odoo employees.

    Shows access events where no employee was found and lets the user
    assign the correct employee. Sets ``idsecure_id`` on the employee
    and reprocesses pending events.
    """

    _name = "idsecure.sync.wizard"
    _description = "iDSecure Employee Mapping Wizard"

    line_ids = fields.One2many(
        "idsecure.sync.wizard.line",
        "wizard_id",
        string="Unmatched Users",
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        # Find distinct unmatched (id_user, name) pairs
        logs = self.env["idsecure.access.log"].read_group(
            domain=[("state", "=", "no_employee"), ("id_user", ">", 0)],
            fields=["id_user", "employee_name_raw"],
            groupby=["id_user", "employee_name_raw"],
            lazy=False,
        )
        lines = []
        seen = set()
        for group in logs:
            id_user = group["id_user"]
            if id_user in seen:
                continue
            seen.add(id_user)
            name = group["employee_name_raw"]
            count = group["__count"]
            # Try to suggest an employee by name
            suggested = self.env["hr.employee"].search(
                [("name", "ilike", name)], limit=1
            )
            lines.append(
                (
                    0,
                    0,
                    {
                        "id_user": id_user,
                        "idsecure_name": name,
                        "pending_count": count,
                        "employee_id": suggested.id if suggested else False,
                    },
                )
            )
        res["line_ids"] = lines
        return res

    def action_apply(self):
        """Apply the mapping: set idsecure_id and reprocess events."""
        self.ensure_one()
        AccessLog = self.env["idsecure.access.log"]
        mapped = 0

        for line in self.line_ids.filtered("employee_id"):
            # Set idsecure_id on the employee
            line.employee_id.write({"idsecure_id": line.id_user})

            # Find and reprocess all pending logs for this id_user
            pending_logs = AccessLog.search(
                [
                    ("id_user", "=", line.id_user),
                    ("state", "in", ("no_employee", "error")),
                ]
            )
            pending_logs.write({"employee_id": line.employee_id.id})
            for log in pending_logs:
                log._process_attendance()
            mapped += 1

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Mapping Complete"),
                "message": _("%d employees mapped and events reprocessed.") % mapped,
                "type": "success",
                "sticky": False,
                "next": {"type": "ir.actions.act_window_close"},
            },
        }


class IDSecureSyncWizardLine(models.TransientModel):
    _name = "idsecure.sync.wizard.line"
    _description = "iDSecure Sync Wizard Line"

    wizard_id = fields.Many2one(
        "idsecure.sync.wizard", required=True, ondelete="cascade"
    )
    id_user = fields.Integer(string="iDSecure User ID", readonly=True)
    idsecure_name = fields.Char(string="Name in iDSecure", readonly=True)
    pending_count = fields.Integer(string="Pending Events", readonly=True)
    employee_id = fields.Many2one("hr.employee", string="Odoo Employee")
