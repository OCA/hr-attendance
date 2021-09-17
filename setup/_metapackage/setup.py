import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo14-addons-oca-hr-attendance",
    description="Meta package for oca-hr-attendance Odoo addons",
    version=version,
    install_requires=[
        'odoo14-addon-hr_attendance_autoclose',
        'odoo14-addon-hr_attendance_modification_tracking',
        'odoo14-addon-hr_attendance_reason',
        'odoo14-addon-hr_attendance_report_theoretical_time',
        'odoo14-addon-hr_attendance_rfid',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
