# Copyright 2025 Binhex <https://www.binhex.cloud>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResourceCalendar(models.Model):
    _inherit = "resource.calendar"

    attendance_before = fields.Float(
        help="This value indicates how much earlier than the scheduled "
        "start time a person can check in. "
        "Enter the time in decimal hours: "
        "for example, 0.25 equals 15 minutes, 0.50 equals 30 minutes, "
        "and 1.00 equals 1 hour early. Only within this range "
        "will clocking in before the actual start time be allowed.\n"
        "Example:\n"
        "\t\tMorning: 08:00 - 12:00\n"
        "\t\tAfternoon: 13:00 - 17:00\n"
        "\t\tTime allowed before: 01:05\n"
        "\t\tThis means that the employee can clock in 1 hour "
        "and 5 minutes before 08:00 y 13:00"
    )
