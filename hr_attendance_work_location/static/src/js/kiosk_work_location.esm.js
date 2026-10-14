/** @odoo-module **/

import {KioskWorkLocation} from "@hr_attendance_work_location/js/kiosk_work_location_component.esm";
import PublicKiosk from "@hr_attendance/public_kiosk/public_kiosk_app";
import {_t} from "@web/core/l10n/translation";
import {patch} from "@web/core/utils/patch";

patch(PublicKiosk.kioskAttendanceApp.prototype, {
    setup() {
        super.setup();
        this.workLocations = [];
        this.workLocationMode = "automatic";
        this.workLocationRequired = false;
        this.defaultWorkLocationId = false;
        this.employeeBarcode = null;
        this._loadKioskLocationSettings();
    },

    async _loadKioskLocationSettings() {
        if (!this.props.token) return;
        const result = await this.rpc(
            "/hr_attendance_work_location/kiosk_location_settings",
            {token: this.props.token}
        );
        if (result) {
            this.workLocationMode = result.work_location_mode;
            this.workLocations = result.work_locations;
            this.workLocationRequired = result.work_location_required;
            this.defaultWorkLocationId = result.default_work_location_id;
        }
    },

    switchDisplay(screen) {
        if (screen === "work_location") {
            this.state.active_display = "work_location";
            return;
        }
        return super.switchDisplay(screen);
    },

    async onBarcodeScanned(barcode) {
        if (this.lockScanner || this.state.active_display !== "main") {
            return;
        }
        if (this.workLocationMode !== "manual") {
            return super.onBarcodeScanned(barcode);
        }
        this.lockScanner = true;
        this.ui.block();
        try {
            const preflight = await this.rpc(
                "/hr_attendance_work_location/attendance_preflight",
                {token: this.props.token, barcode: barcode}
            );
            if (!preflight || !preflight.employee_id) {
                return super.onBarcodeScanned(barcode);
            }
            this.employeeBarcode = barcode;
            this.switchDisplay("work_location");
        } finally {
            this.lockScanner = false;
            this.ui.unblock();
        }
    },

    async kioskConfirm(employeeId) {
        if (this.workLocationMode !== "manual") {
            return super.kioskConfirm(employeeId);
        }
        const employee = await this.rpc("attendance_employee_data", {
            token: this.props.token,
            employee_id: employeeId,
        });
        if (employee && employee.employee_name) {
            if (employee.use_pin) {
                this.employeeData = employee;
                this.switchDisplay("pin");
            } else {
                this.employeeBarcode = null;
                this.employeeId = employeeId;
                this.enteredPin = false;
                this.switchDisplay("work_location");
            }
        }
    },

    async onManualSelection(employeeId, enteredPin) {
        // The PIN pad hands over here, past kioskConfirm: without this step a
        // PIN-protected kiosk in manual mode never offered the location.
        if (this.workLocationMode !== "manual" || !enteredPin) {
            return super.onManualSelection(employeeId, enteredPin);
        }
        const preflight = await this.rpc(
            "/hr_attendance_work_location/attendance_preflight",
            {token: this.props.token, employee_id: employeeId, pin_code: enteredPin}
        );
        if (!preflight || !preflight.employee_id) {
            this.displayNotification(_t("Wrong Pin"));
            return;
        }
        this.employeeBarcode = null;
        this.employeeId = employeeId;
        this.enteredPin = enteredPin;
        this.switchDisplay("work_location");
    },

    async onWorkLocationConfirm(workLocationId) {
        let result = null;
        if (this.employeeBarcode) {
            result = await this.rpc(
                "/hr_attendance_work_location/barcode_with_location",
                {
                    token: this.props.token,
                    barcode: this.employeeBarcode,
                    work_location_id: workLocationId || false,
                }
            );
            this.employeeBarcode = null;
        } else {
            result = await this.makeRpcWithGeolocation("manual_selection", {
                token: this.props.token,
                employee_id: this.employeeId,
                pin_code: this.enteredPin,
                work_location_id: workLocationId || false,
            });
        }
        if (result && result.error) {
            // The server's reason, not a guess: an empty location on a kiosk
            // that requires one is not a wrong PIN.
            this.notification.add(result.message, {type: "danger"});
        } else if (result && result.employee_name) {
            this.employeeData = result;
            this.switchDisplay("greet");
        } else if (this.enteredPin) {
            this.displayNotification(_t("Wrong Pin"));
        }
    },
});

PublicKiosk.kioskAttendanceApp.components = {
    ...PublicKiosk.kioskAttendanceApp.components,
    KioskWorkLocation,
};
