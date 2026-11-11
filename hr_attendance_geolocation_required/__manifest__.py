# Copyright 2025 Álvaro Alonso Bada - Grupo Isonor
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

{
    "name": "HR Attendance Geolocation Required",
    "summary": "This module makes geolocation mandatory for check-in/check-out",
    "author": "Odoo Community Association (OCA),Grupo Isonor",
    "website": "https://github.com/OCA/hr-attendance",
    "license": "LGPL-3",
    "category": "hr_attendance",
    "version": "18.0.1.0.0",
    "depends": ["hr_attendance"],
    "data": [
        "views/res_config_settings_view.xml",
    ],
    "demo": [],
    "assets": {
        "hr_attendance.assets_public_attendance": [
            "hr_attendance_geolocation_required/static/src/public_kiosk/public_kiosk_app.esm.js",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}
