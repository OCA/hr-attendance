import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo14-addons-oca-hr-attendance",
    description="Meta package for oca-hr-attendance Odoo addons",
    version=version,
    install_requires=[
        'odoo14-addon-hr_attendance_reason',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
