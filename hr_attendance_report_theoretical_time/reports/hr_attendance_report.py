# Copyright 2022 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models, tools


class HRAttendanceReport(models.Model):
    _inherit = "hr.attendance.report"

    theoretical_hours = fields.Float(readonly=True)

    # pylint: disable=sql-injection,missing-return
    def init(self):
        """Inject worked_hours field in the query with this hack,fetching the query and
        recreating it.
        TODO: Simplify if merged https://github.com/odoo/odoo/pull/97507
        """
        tools.sql.drop_view_if_exists(self.env.cr, self._table)
        super().init()
        self.env.cr.execute("SELECT pg_get_viewdef(%s, true)", (self._table,))
        view_def = self.env.cr.fetchone()[0]
        view_def = view_def.replace(
            "hra.worked_hours,", "hra.worked_hours, hra.theoretical_hours,"
        )
        view_def = view_def.replace(
            "FROM hr_attendance", ", theoretical_hours FROM hr_attendance"
        )
        if view_def[-1] == ";":
            view_def = view_def[:-1]
        # Re-create view
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute(
            "CREATE OR REPLACE VIEW %s AS ((%s))" % (self._table, view_def)
        )
