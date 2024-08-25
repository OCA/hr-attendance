# Copyright 2023 Janik von Rotz <janik.vonrotz@mint-system.ch>
# Copyright 2024 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "HR Leave Dashboard Extra Time",
    "summary": """
        Display an additional card at the top of the Time Off Dashboard:
        Extra Hours, informing the employee about the number of extra hours
        he has been working and thus the number of hours available
        for him to take as a compensation leave
    """,
    "author": "Mint System GmbH, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/hr-attendance",
    "category": "Human Resources",
    "version": "17.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["hr_holidays_attendance"],
    "installable": True,
    "application": False,
    "auto_install": False,
    "images": ["images/screen.png"],
}
