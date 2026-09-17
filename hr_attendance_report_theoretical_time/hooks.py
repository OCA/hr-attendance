# Copyright 2026 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tools.sql import column_exists


def pre_init_hook(env):
    if not column_exists(env.cr, "hr_attendance", "leave_hours"):
        env.cr.execute(
            """
            ALTER TABLE hr_attendance
            ADD COLUMN IF NOT EXISTS leave_hours double precision
            """,
        )
        env.cr.execute("UPDATE hr_attendance SET leave_hours = 0")
    if not column_exists(env.cr, "hr_attendance", "theoretical_hours"):
        env.cr.execute(
            """
            ALTER TABLE hr_attendance
            ADD COLUMN IF NOT EXISTS theoretical_hours double precision
            """,
        )
        env.cr.execute("UPDATE hr_attendance SET theoretical_hours = 0")
