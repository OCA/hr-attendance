# Copyright 2025 Tecnativa - Eduardo Ezerouali
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
{
    "name": "Hr attendance rest time included",
    "version": "18.0.1.0.0",
    "summary": "Rest time of employee's is included during their working hours",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/hr-attendance",
    "license": "AGPL-3",
    "category": "",
    "depends": ["hr_attendance_reason"],
    "data": [
        "security/ir.model.access.csv",
        "views/hr_attendance_views.xml",
        "views/hr_attendance_rest_time_views.xml",
        "views/hr_attendance_reason_views.xml",
    ],
    "installable": True,
    "application": False,
}
