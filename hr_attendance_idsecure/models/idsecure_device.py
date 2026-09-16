import logging
import re
from datetime import datetime, timedelta, timezone

import pytz
import requests

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from odoo.addons.base.models.res_partner import _tz_get

_logger = logging.getLogger(__name__)

LOGIN_ENDPOINT = "api/login/"
MONITOR_ENDPOINT = "api/access/monitor"
REPORT_LOGS_ENDPOINT = "api/report/logs/global"
USER_ENDPOINT = "api/user/"
GROUP_ENDPOINT = "api/group"
DEFAULT_TIMEOUT = 30


class IDSecureDevice(models.Model):
    _name = "idsecure.device"
    _description = "iDSecure Access Control Server"
    _order = "name"

    # ── Configuration ──────────────────────────────────────────────────
    name = fields.Char(required=True)
    base_url = fields.Char(string="Server URL", required=True)
    username = fields.Char(required=True, default="admin")
    password = fields.Char(required=True)
    timeout = fields.Integer(string="Timeout (s)", default=DEFAULT_TIMEOUT)
    poll_interval = fields.Integer(string="Poll Interval (min)", default=1)
    hours_to_check = fields.Float(string="Hours to Check", default=1.0)
    tz = fields.Selection(
        _tz_get,
        string="Device Timezone",
        required=True,
        default=lambda self: self.env.user.tz or "UTC",
        help="Timezone used by the appliance when it reports event times.\n"
        "The report endpoint returns wall-clock time with no offset, so this\n"
        "is required to convert it to UTC. Leave it as UTC only if the\n"
        "appliance itself is configured in UTC.",
    )
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
    )

    # ── State ──────────────────────────────────────────────────────────
    state = fields.Selection(
        [("draft", "Not Connected"), ("connected", "Connected"), ("error", "Error")],
        default="draft",
        readonly=True,
    )
    last_sync = fields.Datetime(readonly=True)
    last_error = fields.Text(readonly=True)
    access_token = fields.Char(readonly=True, copy=False)

    # ── Mappings ───────────────────────────────────────────────────────
    mapping_ids = fields.One2many(
        "idsecure.company.mapping",
        "device_id",
        string="Company Mappings",
    )

    # ── Statistics ─────────────────────────────────────────────────────
    total_events = fields.Integer(compute="_compute_statistics")
    today_events = fields.Integer(compute="_compute_statistics")
    failed_events = fields.Integer(compute="_compute_statistics")

    @api.depends("name")
    def _compute_statistics(self):
        AccessLog = self.env["idsecure.access.log"]
        today = fields.Datetime.now().replace(hour=0, minute=0, second=0)
        for device in self:
            d = [("device_id", "=", device.id)]
            device.total_events = AccessLog.search_count(d)
            device.today_events = AccessLog.search_count(
                d + [("event_time", ">=", today)]
            )
            device.failed_events = AccessLog.search_count(d + [("state", "=", "error")])

    @api.constrains("base_url")
    def _check_base_url(self):
        for rec in self:
            if rec.base_url and not rec.base_url.startswith(("http://", "https://")):
                raise ValidationError(_("URL must start with http:// or https://"))

    # ══════════════════════════════════════════════════════════════════
    #   API
    # ══════════════════════════════════════════════════════════════════

    def _get_base_url(self):
        return self.base_url.rstrip("/") + "/"

    def _api_login(self):
        self.ensure_one()
        url = self._get_base_url() + LOGIN_ENDPOINT
        payload = {
            "username": self.username,
            "password": self.password,
            "passwordCustom": None,
        }
        try:
            resp = requests.post(url, json=payload, timeout=self.timeout)
            if resp.status_code == 401:
                raise UserError(_("Invalid credentials")) from None
            resp.raise_for_status()
            token = resp.json().get("accessToken")
            if not token:
                raise UserError(_("No accessToken in response"))
            self.sudo().write({"access_token": token})
            return token
        except requests.RequestException as e:
            raise UserError(_("Network error: %s") % e) from e

    def _api_headers(self):
        """Get auth headers, re-login if needed."""
        if not self.access_token:
            self._api_login()
        return {"Authorization": "Bearer %s" % self.access_token}

    def _api_get(self, endpoint, params=None, retry=True):
        """Authenticated GET with auto-retry on 401."""
        url = self._get_base_url() + endpoint
        resp = requests.get(
            url, params=params, headers=self._api_headers(), timeout=self.timeout
        )
        if resp.status_code == 401 and retry:
            self._api_login()
            resp = requests.get(
                url, params=params, headers=self._api_headers(), timeout=self.timeout
            )
        resp.raise_for_status()
        return resp.json()

    def _api_post(self, endpoint, params=None, json_body=None, retry=True):
        """Authenticated POST with auto-retry on 401."""
        url = self._get_base_url() + endpoint
        resp = requests.post(
            url,
            params=params,
            json=json_body,
            headers=self._api_headers(),
            timeout=self.timeout * 3,
        )
        if resp.status_code == 401 and retry:
            self._api_login()
            resp = requests.post(
                url,
                params=params,
                json=json_body,
                headers=self._api_headers(),
                timeout=self.timeout * 3,
            )
        resp.raise_for_status()
        return resp.json()

    def _api_get_access_logs(self, limit=100, initial_date=None, final_date=None):
        """Fetch access logs, using the report endpoint for historical data.

        The monitor endpoint only keeps a small buffer of recent events.
        For date-filtered queries (historical sync / gap recovery) we use
        the report endpoint which has the complete history.
        """
        self.ensure_one()
        if initial_date or final_date:
            return self._api_get_report_logs(
                limit=limit, initial_date=initial_date, final_date=final_date
            )
        # Real-time: use monitor endpoint (fast, small buffer)
        params = {
            "areas": "",
            "events": "",
            "limite": limit,
            "mode": "logs",
            "modevalue": "",
            "parkings": "",
        }
        data = self._api_get(MONITOR_ENDPOINT, params=params)
        return data.get("data", [])

    def _api_get_report_logs(self, limit=10000, initial_date=None, final_date=None):
        """Fetch access logs from the report endpoint (complete history).

        This endpoint uses DataTables server-side pagination and supports
        date filtering via query string parameters.
        """
        self.ensure_one()
        qs_params = {
            "draw": 1,
            "start": 0,
            "length": limit,
            "order[0][column]": 0,
            "order[0][dir]": "desc",
            "columns[0][data]": "time",
        }
        if initial_date:
            qs_params["initialDate"] = initial_date.strftime("%Y-%m-%d")
        if final_date:
            qs_params["finalDate"] = final_date.strftime("%Y-%m-%d")
        body = {
            "cameras": [],
            "areas": [],
            "devices": [],
            "users": [],
            "groups": [],
            "accessLogs": [],
        }
        data = self._api_post(REPORT_LOGS_ENDPOINT, params=qs_params, json_body=body)
        raw_records = data.get("data", [])
        # Normalize field names to match monitor endpoint format
        normalized = []
        for rec in raw_records:
            time_str = rec.get("time", "")
            # Parse "DD/MM/YYYY HH:MM:SS" to datetime
            event_time = False
            if time_str:
                try:
                    event_time = datetime.strptime(time_str, "%d/%m/%Y %H:%M:%S")
                except ValueError:
                    _logger.warning(
                        "Unparseable event time %r from device %s", time_str, self.name
                    )
            normalized.append(
                {
                    "idLog": rec.get("id") or 0,
                    "idUser": rec.get("user_id") or 0,
                    "name": rec.get("user_name", ""),
                    "time": time_str,
                    "_parsed_time": event_time,
                    "eventCode": 0,
                    "eventName": rec.get("event", ""),
                    "device": rec.get("device_name", ""),
                    "area": rec.get("area", ""),
                    "info": rec.get("info", ""),
                    "cardNumberStr": "",
                }
            )
        return normalized

    def _api_get_user(self, user_id):
        """Fetch user details (includes company/group info)."""
        self.ensure_one()
        try:
            return self._api_get(USER_ENDPOINT + str(user_id))
        except Exception as e:
            _logger.debug("Could not fetch user %s: %s", user_id, e)
            return None

    def _api_get_groups(self):
        """Fetch all groups/companies/departments from ControliD."""
        self.ensure_one()
        try:
            return self._api_get(GROUP_ENDPOINT)
        except Exception as e:
            _logger.error("Could not fetch groups: %s", e)
            return []

    # ══════════════════════════════════════════════════════════════════
    #   Actions
    # ══════════════════════════════════════════════════════════════════

    def action_test_connection(self):
        self.ensure_one()
        try:
            self._api_login()
            self.write({"state": "connected", "last_error": False})
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Success"),
                    "message": _("Connected to %s") % self.name,
                    "type": "success",
                    "sticky": False,
                },
            }
        except Exception as e:
            self.write({"state": "error", "last_error": str(e)})
            raise UserError(_("Connection failed: %s") % e) from e

    def action_load_mappings(self):
        """Fetch groups from ControliD and create mapping records."""
        self.ensure_one()
        raw = self._api_get_groups()
        groups = raw.get("data", raw) if isinstance(raw, dict) else raw
        if not groups:
            raise UserError(_("No groups returned from iDSecure API")) from None

        Mapping = self.env["idsecure.company.mapping"]
        created = 0

        for g in groups:
            if not isinstance(g, dict):
                continue
            gid = g.get("id", 0)
            name = g.get("name", "")
            id_type = str(g.get("idType", 0))

            # Skip if mapping already exists
            existing = Mapping.search(
                [
                    ("device_id", "=", self.id),
                    ("idsecure_group_id", "=", gid),
                ],
                limit=1,
            )
            if existing:
                continue

            # Auto-detect import setting
            import_att = True
            if id_type == "1" and name.upper() in ("VISITAS", "FORNECEDORES"):
                import_att = False

            # Auto-detect employee type
            emp_type = "employee"
            if id_type == "1" and name.upper() == "EMPRESAS PARCEIRAS":
                emp_type = "freelancer"

            Mapping.create(
                {
                    "device_id": self.id,
                    "name": name,
                    "idsecure_group_id": gid,
                    "idsecure_id_type": id_type,
                    "import_attendance": import_att,
                    "employee_type": emp_type,
                    "company_id": self.company_id.id,
                }
            )
            created += 1

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Mappings Loaded"),
                "message": _("%d new mappings created from ControliD") % created,
                "type": "success",
                "sticky": False,
            },
        }

    # ══════════════════════════════════════════════════════════════════
    #   Parsing
    # ══════════════════════════════════════════════════════════════════

    def _parse_event_time(self, raw_event):
        """Parse event time from either report or monitor endpoint data.

        The report endpoint returns wall-clock time in the appliance's own
        timezone with no offset, so it must be converted to UTC before Odoo
        stores it. The monitor endpoint returns a .NET epoch, which is
        absolute and needs no conversion.
        """
        # Report endpoint: naive datetime in the device timezone
        parsed = raw_event.get("_parsed_time")
        if parsed:
            return self._device_time_to_utc(parsed)
        # Monitor endpoint: .NET JSON date format
        return self._parse_dotnet_time(raw_event.get("time", ""))

    @staticmethod
    def _parse_dotnet_time(time_str):
        """Parse a .NET JSON date string into a naive UTC datetime.

        The epoch is absolute, so no timezone conversion is needed: the
        offset suffix, when present, is only a display hint.
        """
        if not time_str or "/Date(" not in time_str:
            return False
        match = re.search(r"/Date\((\d+)([+-]\d{4})?\)/", time_str)
        if not match:
            return False
        ts = int(match.group(1)) / 1000
        return datetime.fromtimestamp(ts, tz=timezone.utc).replace(tzinfo=None)

    def _device_time_to_utc(self, naive_dt):
        """Convert a naive datetime in the device timezone to naive UTC."""
        self.ensure_one()
        tz = pytz.timezone(self.tz or "UTC")
        return tz.localize(naive_dt).astimezone(pytz.utc).replace(tzinfo=None)

    @staticmethod
    def _detect_direction(info, event_name):
        text = ((info or "") + " " + (event_name or "")).lower()
        if "entrada" in text or "entry" in text:
            return "entry"
        if "saída" in text or "saida" in text or "exit" in text:
            return "exit"
        return False

    # ══════════════════════════════════════════════════════════════════
    #   Company / Group resolution
    # ══════════════════════════════════════════════════════════════════

    def _get_user_mapping(self, id_user):
        """Fetch user from API and find company mapping.

        Returns (mapping_record, user_data) or (False, None).
        """
        self.ensure_one()
        if not id_user:
            return False, None

        user_data = self._api_get_user(id_user)
        if not user_data:
            return False, None

        groups_list = user_data.get("groupsList", [])
        if not groups_list:
            return False, user_data

        Mapping = self.env["idsecure.company.mapping"]

        # Check companies first (idType=2), then groups (idType=1)
        for id_type in [2, 1, 0]:
            for g in groups_list:
                if g.get("idType") != id_type:
                    continue
                gid = g.get("id", 0)
                # By group ID
                mapping = Mapping.search(
                    [
                        ("device_id", "=", self.id),
                        ("idsecure_group_id", "=", gid),
                    ],
                    limit=1,
                )
                if mapping:
                    return mapping, user_data
                # By name
                mapping = Mapping.search(
                    [
                        ("device_id", "=", self.id),
                        ("name", "=ilike", g.get("name", "")),
                    ],
                    limit=1,
                )
                if mapping:
                    return mapping, user_data

        return False, user_data

    def _should_import(self, id_user):
        """Check if this user should be imported based on company mappings.

        Returns (should_import, employee_type, company_id) or (False, None, None).
        If no mappings are configured, import everything (backward compatible).
        """
        self.ensure_one()

        # If no mappings configured, import everything
        if not self.mapping_ids:
            return True, "employee", self.company_id.id

        mapping, user_data = self._get_user_mapping(id_user)

        if not mapping:
            if user_data is None:
                # API call failed — import with device defaults so events
                # are not silently lost when the user endpoint is down.
                _logger.warning(
                    "User API unavailable for idUser=%s, importing with defaults.",
                    id_user,
                )
                return True, "employee", self.company_id.id
            # User fetched but no matching group — skip
            return False, None, None

        if not mapping.import_attendance:
            return False, None, None

        return True, mapping.employee_type, mapping.company_id.id or self.company_id.id

    # ══════════════════════════════════════════════════════════════════
    #   Employee lookup
    # ══════════════════════════════════════════════════════════════════

    def _find_employee(self, raw_event):
        """Find hr.employee matching an iDSecure event."""
        Employee = self.env["hr.employee"]
        id_user = raw_event.get("idUser", 0)
        card = raw_event.get("cardNumberStr") or ""
        name = raw_event.get("name", "").strip()

        if id_user:
            emp = Employee.search([("idsecure_id", "=", id_user)], limit=1)
            if emp:
                return emp

        if card:
            emp = Employee.search([("barcode", "=", card)], limit=1)
            if emp:
                return emp

        if name:
            emp = Employee.search([("name", "=ilike", name)], limit=1)
            if emp:
                return emp
            emp = Employee.search([("name", "ilike", name)], limit=1)
            if emp:
                _logger.warning(
                    "Partial name match '%s' -> '%s'. Set idsecure_id=%s.",
                    name,
                    emp.name,
                    id_user,
                )
                return emp

        return Employee

    # ══════════════════════════════════════════════════════════════════
    #   Sync
    # ══════════════════════════════════════════════════════════════════

    @api.model
    def cron_sync_all_devices(self):
        devices = self.search([("active", "=", True)])
        for device in devices:
            try:
                device.action_sync_access_events()
            except Exception as e:
                _logger.error("Sync failed for %s: %s", device.name, e)
                device.sudo().write({"state": "error", "last_error": str(e)[:500]})

    def action_sync_access_events(self, limit=100, initial_date=None, final_date=None):
        self.ensure_one()
        _logger.info("iDSecure sync for '%s'", self.name)

        # Use hours_to_check window when no explicit dates are given.
        # If last_sync is older than hours_to_check, extend the window
        # back to last_sync so that gap days are recovered automatically.
        if not initial_date and self.hours_to_check:
            default_start = fields.Datetime.now() - timedelta(hours=self.hours_to_check)
            if self.last_sync and self.last_sync < default_start:
                initial_date = self.last_sync
                limit = max(limit, 5000)
                _logger.info(
                    "Gap detected for '%s': last_sync=%s, extending window.",
                    self.name,
                    self.last_sync,
                )
            else:
                initial_date = default_start

        raw_logs = self._api_get_access_logs(
            limit=limit, initial_date=initial_date, final_date=final_date
        )
        if not raw_logs:
            self.sudo().write(
                {"last_sync": fields.Datetime.now(), "state": "connected"}
            )
            return

        AccessLog = self.env["idsecure.access.log"]
        created = skipped = filtered = errors = 0
        last_error_msg = False

        # Cache: user_id -> (should_import, emp_type, company_id)
        import_cache = {}

        for raw in raw_logs:
            id_log = raw.get("idLog", 0)
            id_user = raw.get("idUser", 0)

            # Dedup: by id_log when available, otherwise by user+time
            if id_log:
                if AccessLog.search(
                    [("device_id", "=", self.id), ("id_log", "=", id_log)], limit=1
                ):
                    skipped += 1
                    continue
            else:
                # Report endpoint has no idLog — dedup by user + event_time
                event_time = self._parse_event_time(raw)
                if event_time and AccessLog.search(
                    [
                        ("device_id", "=", self.id),
                        ("id_user", "=", id_user),
                        ("event_time", "=", event_time),
                    ],
                    limit=1,
                ):
                    skipped += 1
                    continue

            # Company filter (with cache)
            if id_user not in import_cache:
                import_cache[id_user] = self._should_import(id_user)

            should_import, emp_type, comp_id = import_cache[id_user]
            if not should_import:
                filtered += 1
                continue

            # Parse and create inside a savepoint so one bad event
            # does not rollback the entire batch and block future syncs.
            try:
                with self.env.cr.savepoint():
                    event_time = self._parse_event_time(raw)
                    direction = self._detect_direction(
                        raw.get("info"), raw.get("eventName")
                    )
                    employee = self._find_employee(raw)

                    vals = {
                        "device_id": self.id,
                        "id_log": id_log,
                        "employee_id": employee.id if employee else False,
                        "employee_name_raw": raw.get("name", ""),
                        "id_user": id_user,
                        "event_time": event_time or fields.Datetime.now(),
                        "direction": direction or "entry",
                        "event_code": raw.get("eventCode", 0),
                        "event_name": raw.get("eventName", ""),
                        "device_name": raw.get("device", ""),
                        "area_name": raw.get("area", ""),
                        "info": raw.get("info", ""),
                        "card_number": raw.get("cardNumberStr") or "",
                        "raw_data": str(raw),
                    }

                    log_record = AccessLog.create(vals)
                    created += 1
                    log_record._process_attendance()
            except Exception as e:
                errors += 1
                last_error_msg = str(e)[:500]
                _logger.error(
                    "iDSecure event error (device=%s, idLog=%s): %s",
                    self.name,
                    id_log,
                    e,
                )

        _logger.info(
            "Sync '%s': %d created, %d skipped, %d filtered, %d errors",
            self.name,
            created,
            skipped,
            filtered,
            errors,
        )
        sync_vals = {
            "last_sync": fields.Datetime.now(),
            "state": "connected",
        }
        if errors:
            sync_vals["last_error"] = _(
                "%(errors)d of %(total)d events failed. Last: %(msg)s",
                errors=errors,
                total=created + errors,
                msg=last_error_msg,
            )
        else:
            sync_vals["last_error"] = False
        self.sudo().write(sync_vals)
