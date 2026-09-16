import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class IDSecureAccessLog(models.Model):
    """Raw access event received from an iDSecure device.

    Each record represents one turnstile passage (entry or exit).
    The ``_process_attendance`` method converts it into an ``hr.attendance``
    check-in or check-out.
    """

    _name = "idsecure.access.log"
    _description = "iDSecure Access Event"
    _order = "event_time desc, id desc"
    _rec_name = "display_name"

    # ── Source identification ──────────────────────────────────────────
    device_id = fields.Many2one(
        "idsecure.device",
        string="iDSecure Server",
        required=True,
        ondelete="cascade",
        index=True,
    )
    id_log = fields.Integer(
        string="iDSecure Log ID",
        required=True,
        index=True,
        help="idLog from iDSecure — unique per device, used for deduplication",
    )

    # ── Employee ──────────────────────────────────────────────────────
    employee_id = fields.Many2one(
        "hr.employee",
        string="Employee",
        index=True,
        help="Matched Odoo employee. Empty if no match was found.",
    )
    employee_name_raw = fields.Char(
        string="Name (iDSecure)",
        help="Original name as reported by the access control system",
    )
    id_user = fields.Integer(
        string="iDSecure User ID",
        index=True,
        help="idUser from iDSecure — stable ID for the person",
    )

    # ── Event details ─────────────────────────────────────────────────
    event_time = fields.Datetime(
        required=True,
        index=True,
    )
    direction = fields.Selection(
        [("entry", "Entry"), ("exit", "Exit")],
        required=True,
        index=True,
    )
    event_code = fields.Integer()
    event_name = fields.Char()
    device_name = fields.Char()
    area_name = fields.Char()
    info = fields.Char()
    card_number = fields.Char()

    # ── Processing state ──────────────────────────────────────────────
    state = fields.Selection(
        [
            ("pending", "Pending"),
            ("done", "Registered"),
            ("no_employee", "Employee Not Found"),
            ("error", "Error"),
        ],
        string="Status",
        default="pending",
        required=True,
        index=True,
    )
    attendance_id = fields.Many2one(
        "hr.attendance",
        string="Attendance Record",
        readonly=True,
        help="The hr.attendance record created or updated by this event",
    )
    error_message = fields.Text(readonly=True)

    # ── Audit ─────────────────────────────────────────────────────────
    raw_data = fields.Text()

    # ── Display ───────────────────────────────────────────────────────
    display_name = fields.Char(compute="_compute_display_name", store=True)

    @api.depends("employee_name_raw", "direction", "event_time")
    def _compute_display_name(self):
        for rec in self:
            direction = _("Entry") if rec.direction == "entry" else _("Exit")
            rec.display_name = "%s — %s — %s" % (
                rec.employee_name_raw or _("Unknown"),
                direction,
                rec.event_time or "",
            )

    # ── SQL constraint for dedup ──────────────────────────────────────
    # id_log=0 means the record came from the report endpoint (no idLog).
    # We only enforce uniqueness when id_log is set.
    _sql_constraints = []

    def init(self):
        """Create partial unique index excluding report-only records."""
        self.env.cr.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
                idsecure_access_log_unique_device_idlog
            ON idsecure_access_log (device_id, id_log)
            WHERE id_log != 0
        """
        )

    # ══════════════════════════════════════════════════════════════════
    #   Attendance processing
    # ══════════════════════════════════════════════════════════════════

    def _process_attendance(self):
        """Convert this access event into an hr.attendance action.

        Entry → create new hr.attendance (check_in)
        Exit  → close the latest open hr.attendance (check_out)

        When direction cannot be determined from the device data, use
        toggle logic: if the employee has an open attendance → check_out,
        otherwise → check_in.

        If no employee is matched, the record is marked 'no_employee'.
        """
        self.ensure_one()

        if not self.employee_id:
            self.write(
                {
                    "state": "no_employee",
                    "error_message": _(
                        "No employee found for '%(name)s' (iDSecure user ID: %(uid)s)",
                        name=self.employee_name_raw,
                        uid=self.id_user,
                    ),
                }
            )
            return

        direction = self.direction
        if not self._has_reliable_direction():
            direction = self._infer_direction()
            if direction != self.direction:
                self.write({"direction": direction})

        try:
            if direction == "entry":
                self._do_check_in()
            else:
                self._do_check_out()
        except Exception as e:
            _logger.error(
                "iDSecure attendance error for %s: %s",
                self.employee_name_raw,
                e,
            )
            error_msg = str(e)
            # Odoo duplicate attendance errors — treat as success
            if self._is_duplicate_error(error_msg):
                self.write({"state": "done", "error_message": False})
            else:
                self.write({"state": "error", "error_message": error_msg[:500]})
                self._notify_hr_attendance_error(error_msg)

    def _has_reliable_direction(self):
        """Check if the direction was detected from actual device data.

        Events with info containing 'Entrada'/'Saída' have reliable direction.
        Events from the report endpoint (info empty, eventName='Autorizado')
        do not — they were defaulted to 'entry' during sync.
        """
        self.ensure_one()
        info = (self.info or "").lower()
        event = (self.event_name or "").lower()
        return (
            "entrada" in info
            or "saída" in info
            or "saida" in info
            or "entry" in info
            or "exit" in info
            or "entrada" in event
            or "saída" in event
            or "saida" in event
        )

    def _infer_direction(self):
        """Infer direction using toggle logic based on open attendances.

        If the employee has an open attendance (check_in without check_out),
        this event is a check_out (exit). Otherwise it is a check_in (entry).
        """
        self.ensure_one()
        open_att = self.env["hr.attendance"].search(
            [
                ("employee_id", "=", self.employee_id.id),
                ("check_out", "=", False),
            ],
            limit=1,
        )
        direction = "exit" if open_att else "entry"
        _logger.debug(
            "Inferred direction '%s' for %s (open attendance: %s)",
            direction,
            self.employee_name_raw,
            bool(open_att),
        )
        return direction

    def _do_check_in(self):
        """Create a new hr.attendance record with check_in."""
        Attendance = self.env["hr.attendance"]
        attendance = Attendance.create(
            {
                "employee_id": self.employee_id.id,
                "check_in": self.event_time,
            }
        )
        _logger.info(
            "Check-in created for %s at %s (attendance %s)",
            self.employee_id.name,
            self.event_time,
            attendance.id,
        )
        self.write(
            {
                "state": "done",
                "attendance_id": attendance.id,
                "error_message": False,
            }
        )

    def _do_check_out(self):
        """Find the latest open attendance for this employee and close it."""
        Attendance = self.env["hr.attendance"]
        open_att = Attendance.search(
            [
                ("employee_id", "=", self.employee_id.id),
                ("check_out", "=", False),
            ],
            order="check_in desc",
            limit=1,
        )
        if not open_att:
            _logger.warning(
                "Check-out for %s at %s but no open attendance found. "
                "Event logged for manual review.",
                self.employee_id.name,
                self.event_time,
            )
            self.write(
                {
                    "state": "error",
                    "error_message": _(
                        "Check-out without prior check-in. "
                        "Please create or correct the attendance manually."
                    ),
                }
            )
            return

        open_att.write({"check_out": self.event_time})
        _logger.info(
            "Check-out registered for %s at %s (attendance %s)",
            self.employee_id.name,
            self.event_time,
            open_att.id,
        )
        self.write(
            {
                "state": "done",
                "attendance_id": open_att.id,
                "error_message": False,
            }
        )

    @staticmethod
    def _is_duplicate_error(msg):
        """Detect Odoo's own duplicate / overlap attendance errors.

        We must NOT treat "não comparece ao trabalho" (employee has not
        attended since …) as a duplicate — that is a real attendance gap
        that HR needs to resolve.
        """
        msg_lower = msg.lower()
        # Exclude real attendance-gap errors from being silenced
        if "não comparece ao trabalho" in msg_lower:
            return False
        keywords = [
            "cannot create",
            "já bateu",
            "already",
            "não é possível",
            "presença",
            "overlap",
        ]
        return any(kw in msg_lower for kw in keywords)

    # ══════════════════════════════════════════════════════════════════
    #   HR Notification
    # ══════════════════════════════════════════════════════════════════

    def _notify_hr_attendance_error(self, error_msg):
        """Post an internal note on the employee record so HR is notified."""
        if not self.employee_id:
            return
        try:
            body = _(
                "<b>Erro de Presença (iDSecure)</b><br/>"
                "Funcionário: <b>%(employee)s</b><br/>"
                "Evento: %(direction)s em %(time)s<br/>"
                "Erro: %(error)s<br/>"
                "<br/>"
                "Por favor, verifique e corrija o registro de presença manualmente.",
                employee=self.employee_id.name,
                direction=_("Entrada") if self.direction == "entry" else _("Saída"),
                time=self.event_time,
                error=error_msg[:200],
            )
            self.employee_id.sudo().message_post(
                body=body,
                subject=_("Erro de Presença - %s") % self.employee_id.name,
                message_type="notification",
                subtype_xmlid="mail.mt_note",
            )
        except Exception:
            _logger.warning(
                "Could not send HR notification for employee %s",
                self.employee_id.name,
                exc_info=True,
            )

    # ══════════════════════════════════════════════════════════════════
    #   Actions (buttons)
    # ══════════════════════════════════════════════════════════════════

    def action_retry(self):
        """Retry processing for failed events."""
        for rec in self.filtered(lambda r: r.state in ("error", "no_employee")):
            # Re-attempt employee match if missing
            if not rec.employee_id:
                employee = rec.device_id._find_employee(
                    {
                        "idUser": rec.id_user,
                        "cardNumberStr": rec.card_number,
                        "name": rec.employee_name_raw,
                    }
                )
                if employee:
                    rec.employee_id = employee
            rec._process_attendance()
