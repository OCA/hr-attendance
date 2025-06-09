# Copyright 2025 Álvaro Alonso Bada - Grupo Isonor
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

{
    "name": "HR Attendance Geolocation Required",
    "summary": "Hace obligatoria la geolocalización para fichar en Odoo 17",
    "author": "Odoo Community Association (OCA),Grupo Isonor",
    "website": "https://github.com/OCA/hr-attendance",
    "license": "LGPL-3",
    "category": "hr_attendance",
    "version": "17.0.1.0.0",
    "depends": ["hr_attendance"],
    "data": [],
    "demo": [],
    "assets": {
        "web.assets_backend": [
            "hr_attendance_geolocation_required/static/src/public_kiosk/public_kiosk_app.js",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}
