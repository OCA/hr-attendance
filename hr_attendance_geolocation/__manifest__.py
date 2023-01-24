# Copyright 2019 ForgeFlow S.L.
# Copyright 2023 Tecnativa
# Copyright 2023 Grupo Isonor
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Hr Attendance Geolocation",
    "summary": """
        With this module the geolocation of the user is tracked at the
        check-in/check-out step""",
    "version": "15.0.1.0.3",
    "license": "AGPL-3",
    "author": "ForgeFlow S.L., Tecnativa, Grupo Isonor, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/hr-attendance",
    "depends": ["hr_attendance"],
    "data": [
        "views/hr_attendance_views.xml",
        "data/location_data.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "hr_attendance_geolocation/static/src/js/geolocation_user_context_legacy.esm.js",
            "hr_attendance_geolocation/static/src/js/geolocation_service_legacy.js",
            "hr_attendance_geolocation/static/src/js/attendance_geolocation.js",
        ],
    },
}
