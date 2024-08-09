/** @odoo-module **/

import {KioskReason} from "@hr_attendance_reason/components/kiosk_reason/kiosk_reason.esm";
import PublicKiosk from "@hr_attendance/public_kiosk/public_kiosk_app";
import {patch} from "@web/core/utils/patch";

patch(PublicKiosk.kioskAttendanceApp.prototype, {
    setup() {
        super.setup();
        this.getKioskReasonSettings();
        this.show_attendance_reason_screen = true;
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
            const employee = await this.rpc("/hr_attendance_reason/get_reasons", {
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
        return super.onManualSelection(employeeId, enteredPin);
    },
    async getKioskReasonSettings() {
        const result = await this.rpc("/hr_attendance_reason/reason_settings", {
            token: this.props.token,
        });
        this.show_reason_on_attendance_screen = result.show_reason_on_attendance_screen;
    },
    async onReasonSelection(employeeId, pin_code) {
        // Set the show_attendance_reason_screen
        // for when onManualSelection is called,
        // the 'reason' screen will not be displayed again.
        this.show_attendance_reason_screen = false;
        await this.onManualSelection(employeeId, pin_code);
        this.show_attendance_reason_screen = true;
    },
});

PublicKiosk.kioskAttendanceApp.components = {
    ...PublicKiosk.kioskAttendanceApp.components,
    KioskReason,
};
