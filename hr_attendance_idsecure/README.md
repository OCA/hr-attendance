# HR Attendance - iDSecure Integration

[![License: AGPL-3](https://img.shields.io/badge/licence-AGPL--3-blue.svg)](http://www.gnu.org/licenses/agpl-3.0-standalone.html)

Automatic employee attendance registration from **ControliD iDSecure** access control
systems. No external middleware required — runs natively inside Odoo.

## About ControliD / iDSecure

[Control iD](https://www.controlid.com.br/en/) is a Brazilian manufacturer of access
control and time & attendance devices, part of the
[ASSA ABLOY](https://www.assaabloy.com/) group. Their **iDSecure** software platform
manages all ControliD access controllers via a web-based interface and REST API.

### Compatible Devices

This module works with **any device managed by iDSecure** (On-Premises or Cloud),
including the full ControliD product line:

**Facial Recognition:**

- **iDFace** — Dual 1080p cameras, liveness detection, up to 10,000 faces, IP65
- **iDFace Max** — 7" touchscreen, up to 100,000 faces, PoE support, IP65

**Turnstiles:**

- **iDBlock Next** — Smart turnstile with integrated iDFace (up to 2 units)
- **iDBlock Black / Stainless Steel** — Digital biometric turnstiles
- **iDBlock Bridge-Type** — Bridge-type biometric turnstile
- **iDBlock Drop Arm** — Drop arm turnstile
- **iDBlock Handicapped Accessible** — Accessible biometric gate

**Access Controllers:**

- **iDAccess / iDAccess Pro** — Biometric + card access control
- **iDAccess Nano** — Compact slave access controller
- **iDFlex / iDFlex Pro** — Multifunctional controller with fingerprint, up to 6,000
  templates
- **iDBox** — Multi-door controller (up to 4 doors, 200,000 users)

**Readers & Peripherals:**

- **iDTouch** — Capacitive keyboard + proximity reader
- **iDProx / iDProx Slim** — Proximity card readers (MIFARE / 125kHz ASK / HID)
- **iDUHF / iDUHF Lite** — UHF vehicle tag readers
- **iDLock / iDLock Bio** — Digital door locks

**Identification Methods Supported:**

- Facial recognition (with mask detection and liveness)
- Fingerprint biometrics
- Proximity cards (MIFARE, 125kHz ASK, HID)
- PIN / password
- QR Code
- UHF vehicle tags

## How it works

```
Device (facial recognition / fingerprint / card / PIN)
    ↓
iDSecure Server (ControliD)
    ↓  ← Odoo cron polls every minute
Odoo (this module)
    ↓
hr.attendance records
```

A cron job connects to the iDSecure REST API, fetches new access events, matches each
event to an `hr.employee`, and creates/closes `hr.attendance` records.

## Features

- **Zero middleware** — no Docker, Flask, SQLite, or XML-RPC bridge needed
- **Company mapping** — map ControliD companies to Odoo companies + employee types
- **Visitor/supplier filtering** — automatically skip non-employees
- **Reliable employee matching** — by iDSecure ID, barcode, exact name, or partial name
- **Full audit trail** — every raw event stored with processing state and link to
  attendance
- **Employee mapping wizard** — bulk-assign iDSecure IDs to employees
- **Retry mechanism** — reprocess failed events with one click
- **Multi-device** — supports multiple iDSecure servers
- **38 unit tests**

## Configuration

### Device Setup

1. Go to **Attendances → iDSecure → Devices**
2. Create device with your iDSecure server URL and credentials
3. Click **Test Connection**

### Company Mappings

1. Open device form → **Company Mappings** tab
2. Click **Load from ControliD** (auto-fetches all groups/companies from the API)
3. Configure each mapping:

| ControliD Name | Type    | Odoo Company | Employee Type | Import? |
| -------------- | ------- | ------------ | ------------- | ------- |
| MCP            | Company | MCP Yachts   | Employee      | ✅      |
| RM             | Company | MCP Yachts   | Employee      | ✅      |
| Offshore II    | Company | Offshore II  | Employee      | ✅      |
| Gmar           | Company | MCP Yachts   | Freelancer    | ✅      |
| VISITAS        | Group   | —            | —             | ❌      |
| FORNECEDORES   | Group   | —            | —             | ❌      |

### Employee Mapping

For reliable matching, set **iDSecure ID** on each employee:

- Go to **Employees → HR Settings → iDSecure ID** (the `idUser` from ControliD)
- Or use **Attendances → iDSecure → Map Employees** wizard for bulk assignment

## Attendance Logic

| Event                        | Action                                                        |
| ---------------------------- | ------------------------------------------------------------- |
| Entry (Entrada)              | Creates `hr.attendance` with `check_in`                       |
| Exit (Saída)                 | Closes the latest open `hr.attendance` with `check_out`       |
| Exit without open attendance | Marked as **error** for manual review (never fabricates data) |

## iDSecure API Endpoints Used

| Endpoint              | Method | Purpose                                         |
| --------------------- | ------ | ----------------------------------------------- |
| `/api/login/`         | POST   | Authentication (returns JWT access token)       |
| `/api/access/monitor` | GET    | Fetch access events with pagination             |
| `/api/user/<id>`      | GET    | User details including company/group membership |
| `/api/group`          | GET    | List all companies, departments and groups      |

## Technical Notes

- Events are deduplicated by `(device_id, id_log)` SQL constraint
- Cron runs every minute by default (configurable in Scheduled Actions)
- Datetimes from iDSecure `.NET /Date(timestamp-offset)/` format are parsed as UTC
- Company filtering uses the iDSecure user API with in-memory caching per sync cycle
- Requires `requests` Python library (standard in most Odoo deployments)
- Compatible with iDSecure On-Premises and iDSecure Cloud

## Credits

### Authors

- Pop Solutions

### Contributors

- Marcos Méndez

## License

This module is licensed under AGPL-3.
