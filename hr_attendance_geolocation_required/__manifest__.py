# Grupo Isonor
# Copyright (C) All Rights Reserved

{
    "name": "HR Attendance Geolocation Required",
    "summary": "Hace obligatoria la geolocalización para fichar en Odoo 17",
    "author": "Odoo Community Association (OCA),Grupo Isonor, Álvaro Alonso",
    "website": "https://github.com/OCA/hr-attendance",
    "license": "LGPL-3",
    "category": "hr_attendance",
    "version": "17.0.1.0.0",
    "depends": ["hr_attendance"],
    "data": [],
    "assets": {
        "web.assets_backend": [
            "hr_attendance_geolocation_required/static/src/public_kiosk/public_kiosk_app.js",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}
