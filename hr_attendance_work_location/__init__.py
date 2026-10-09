from . import controllers
from . import models


def post_init_hook(env):
    """Set default work_location_mode='automatic' for existing companies."""
    companies = env["res.company"].search([("work_location_mode", "=", False)])
    companies.write({"work_location_mode": "automatic"})
