# Copyright 2025 ForgeFlow, S.L.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl-3.0).
{
    "name": "Attendance Work Model",
    "summary": """
        Trace the Work Model of the attendances
    """,
    "version": "17.0.1.0.0",
    "category": "Human Resources",
    "website": "https://github.com/OCA/hr-attendance",
    "author": "ForgeFlow S.L., Odoo Community Association (OCA)",
    "maintainers": ["GuillemCForgeFlow"],
    "license": "LGPL-3",
    "depends": ["hr_attendance"],
    "data": [
        "security/ir.model.access.csv",
        "views/hr_attendance_views.xml",
        "views/res_company_views.xml",
    ],
}
