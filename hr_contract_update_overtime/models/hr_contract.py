# Copyright 2024 Moduon Team S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)
from datetime import datetime, timedelta

from odoo import _, fields, models


class HrContract(models.Model):
    _inherit = "hr.contract"

    def _get_attendances(self):
        self.ensure_one()
        dtt_start = datetime.combine(self.date_start, datetime.min.time())
        dtt_end = datetime.combine(
            self.date_end or fields.Date.today(), datetime.min.time()
        )
        return self.employee_id.attendance_ids.filtered(
            lambda att: att.check_in >= dtt_start
            and att.check_in < (dtt_end + timedelta(days=1))
        )

    def action_update_overtime(self):
        for record in self:
            if record.state not in {"open", "close"}:
                continue
            attendances = record._get_attendances()
            attendances._update_overtime()
            record.message_post(
                body=_("Overtime updated"),
                subtype_xmlid="mail.mt_note",
                message_type="comment",
                author_id=self.env.user.partner_id.id,
            )
