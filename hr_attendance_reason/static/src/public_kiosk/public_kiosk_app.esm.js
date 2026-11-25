import {KioskReason} from "@hr_attendance_reason/components/kiosk_reason/kiosk_reason.esm";
import {patch} from "@web/core/utils/patch";
import PublicKiosk from "@hr_attendance/public_kiosk/public_kiosk_app";
import {rpc} from "@web/core/network/rpc";

patch(PublicKiosk.kioskAttendanceApp.prototype, {
    setup() {
        super.setup();
        this.getKioskReasonSettings();
        this.show_attendance_reason_screen = true;
        this.attendance_reason_id = "";
    },
    switchDisplay(screen) {
        if (screen === "reason") {
            this.state.active_display = screen;
            return;
        }
        return super.switchDisplay(screen);
    },
    async onManualSelection(employeeId, enteredPin) {
        // Check if is need to show the reason screen
        if (
            this.show_reason_on_attendance_screen &&
            this.show_attendance_reason_screen
        ) {
            const employee = await rpc("/hr_attendance_reason/get_reasons", {
                token: this.props.token,
                employee_id: employeeId,
                pin_code: enteredPin,
            });
            if (employee && employee.employee_name) {
                this.employeeData = employee;
                this.reasons = employee.reasons;
                this.pin_code = enteredPin;
                return this.switchDisplay("reason");
            }
        }
        // No reason screen needed (or already answered): continue with core flow
        return super.onManualSelection(employeeId, enteredPin);
    },
    // Core builds the manual_selection call itself, so the reason is injected here
    async makeRpcWithGeolocation(route, params) {
        const extraParams =
            route === "manual_selection" && this.attendance_reason_id
                ? {attendance_reason_id: this.attendance_reason_id}
                : {};
        return super.makeRpcWithGeolocation(route, {...params, ...extraParams});
    },
    async getKioskReasonSettings() {
        const result = await rpc("/hr_attendance_reason/reason_settings", {
            token: this.props.token,
        });
        this.show_reason_on_attendance_screen = result.show_reason_on_attendance_screen;
    },
    async onReasonSelection(employeeId, pin_code, attendance_reason_id) {
        // Set the show_attendance_reason_screen
        // for when onManualSelection is called,
        // the 'reason' screen will not be displayed again.
        this.show_attendance_reason_screen = false;
        this.attendance_reason_id =
            attendance_reason_id === "0" ? "" : attendance_reason_id;
        try {
            await this.onManualSelection(employeeId, pin_code);
        } finally {
            this.show_attendance_reason_screen = true;
            this.attendance_reason_id = "";
        }
    },
});

PublicKiosk.kioskAttendanceApp.components = {
    ...PublicKiosk.kioskAttendanceApp.components,
    KioskReason,
};
