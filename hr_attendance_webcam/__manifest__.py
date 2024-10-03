# Copyright 2024 Binhex - Adasat Torres de León.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)

{
    "name": "Attendance Webcam",
    "summary": """
        This addon allows you to take a picture of the employee when they check in/out.
    """,
    "author": "Binhex, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/hr-attendance",
    "license": "AGPL-3",
    "category": "Human Resources",
    "version": "16.0.1.0.0",
    "depends": ["hr_attendance"],
    "data": [
        "security/hr_attendance_security.xml",
        "views/hr_attendance_view.xml",
        "views/res_config_settings_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "hr_attendance_webcam/static/src/**/*",
        ],
    },
}
