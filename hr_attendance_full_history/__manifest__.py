# Copyright 2026 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

{
    "name": "HR Attendance Full History",
    "summary": "Let employees read their full attendance history",
    "version": "18.0.1.0.0",
    "development_status": "Alpha",
    "category": "Human Resources/Attendances",
    "website": "https://github.com/OCA/hr-attendance",
    "author": "Moduon, Odoo Community Association (OCA)",
    "maintainers": ["rblasco", "yajo"],
    "license": "LGPL-3",
    "installable": True,
    "depends": ["hr_attendance"],
    "data": [
        "views/res_users_view.xml",
    ],
}
