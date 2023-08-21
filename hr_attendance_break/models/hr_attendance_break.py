# Copyright 2023 Hunki Enterprises BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)


from odoo import _, api, exceptions, fields, models


class HrAttendanceBreak(models.Model):
    _name = "hr.attendance.break"
    _rec_name = "attendance_id"
    _description = "Work break taken"
    _order = "begin desc"

    attendance_id = fields.Many2one("hr.attendance", required=True, ondelete="cascade")
    begin = fields.Datetime(required=True)
    end = fields.Datetime(required=False)
    break_hours = fields.Float(compute="_compute_break_hours")
    reason_id = fields.Many2one("hr.attendance.reason")

    @api.constrains("attendance_id", "begin", "end")
    def _check_times(self):
        for this in self:
            valid = True
            if this.attendance_id.check_in and this.begin:
                valid &= this.attendance_id.check_in <= this.begin
            if this.attendance_id.check_out and this.end:
                valid &= this.attendance_id.check_out >= this.end
            if valid and this.begin and this.end:
                valid &= not bool(
                    self.search_count(
                        [
                            ("begin", "<", this.end),
                            ("end", ">", this.begin),
                            ("id", "not in", this.ids),
                            ("attendance_id", "=", this.attendance_id.id),
                        ]
                    )
                )
                valid &= this.begin < this.end
            if not valid:
                raise exceptions.ValidationError(
                    _(
                        "Breaks must be fully contained by the attendance they belong to "
                        "and can't overlap"
                    )
                )

    @api.depends("begin", "end")
    def _compute_break_hours(self):
        for this in self:
            this.break_hours = (
                0 if not this.end else (this.end - this.begin).total_seconds() / 3600
            )

    @api.model_create_multi
    def create(self, vals_list):
        result = super().create(vals_list)
        result.mapped("attendance_id")._update_overtime()
        return result

    def write(self, vals):
        result = super().write(vals)
        if {"attendance_id", "begin", "end"} & set(vals):
            self.mapped("attendance_id")._update_overtime()
        return result

    def unlink(self):
        to_update = self.mapped("attendance_id")
        result = super().unlink()
        to_update._update_overtime()
        return result
