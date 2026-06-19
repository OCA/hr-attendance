{
    "name": "HR Attendance Geolocation Required",
    "summary": "Make geolocation mandatory for attendance check-in/check-out",
    "category": "Human Resources/Attendances",
    "version": "16.0.1.0.0",
    "license": "LGPL-3",
    "author": "Odoo Community Association (OCA), Grupo Isonor",
    "website": "https://github.com/OCA/hr-attendance",
    "depends": ["hr_attendance"],
    "data": [
        "views/res_config_settings_view.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "hr_attendance_geolocation_required/static/src/public_kiosk/public_kiosk_app.esm.js",  # noqa: B950
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}
