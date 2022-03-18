# -*- coding: utf-8 -*-
{
    "name": "Attendance Geofence",
    "description": """to get location of employee and check if employee is in the geofence or not""",
    "version": "15.0.1.0.3",
    'author': 'Nanda',
    'company': 'Nanda',
    'maintainer': 'Nanda',
    "depends": ['base', 'hr_attendance'],
    "data": [
        'views/icons.xml',
        'views/layout.xml',
    ],
    # 'assets': {
    #     'web.assets_frontend': [
    #         'code_backend_theme/static/src/scss/login.scss',
    #     ],
    #     'web.assets_backend': [
    #         'code_backend_theme/static/src/scss/theme_accent.scss',
    #         'code_backend_theme/static/src/scss/navigation_bar.scss',
    #         'code_backend_theme/static/src/scss/datetimepicker.scss',
    #         'code_backend_theme/static/src/scss/theme.scss',
    #         'code_backend_theme/static/src/scss/sidebar.scss',

    #         'code_backend_theme/static/src/js/fields/colors.js',
    #         'code_backend_theme/static/src/js/chrome/sidebar_menu.js',
    #     ],
    #     'web.assets_qweb': [
    #         'code_backend_theme/static/src/xml/styles.xml',
    #         'code_backend_theme/static/src/xml/top_bar.xml',
    #     ],
    # },
    'installable': True,
    'application': False,
    'auto_install': False,
}
