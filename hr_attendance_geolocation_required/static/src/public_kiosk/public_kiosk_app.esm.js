/** @odoo-module **/

import {_t} from "@web/core/l10n/translation";
import {patch} from "@web/core/utils/patch";

import PublicKiosk from "@hr_attendance/public_kiosk/public_kiosk_app";

class NoGeolocationError extends Error {}

patch(PublicKiosk.kioskAttendanceApp.prototype, {
    async makeRpcWithGeolocation(route, params) {
        const result = await super.makeRpcWithGeolocation(route, params);
        if (result.error) {
            this.displayNotification(_t("Error: %s", result.error));
            throw new NoGeolocationError();
        }
        return result;
    },

    async onManualSelection(employeeId, enteredPin) {
        try {
            await super.onManualSelection(employeeId, enteredPin);
        } catch (err) {
            if (!(err instanceof NoGeolocationError)) {
                throw err;
            }
        }
    },
});
