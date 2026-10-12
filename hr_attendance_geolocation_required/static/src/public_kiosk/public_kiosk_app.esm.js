/* @odoo-module */

import PublicKiosk from "@hr_attendance/public_kiosk/public_kiosk_app";
import {_t} from "@web/core/l10n/translation";
import {patch} from "@web/core/utils/patch";

patch(PublicKiosk.kioskAttendanceApp.prototype, {
    _geolocationError: false,

    async makeRpcWithGeolocation(route, params) {
        const result = await super.makeRpcWithGeolocation(route, params);
        if (result && result.error) {
            this.displayNotification(_t(result.error));
            this._geolocationError = true;
            return result;
        }
        this._geolocationError = false;
        return result;
    },

    async onManualSelection(employeeId, enteredPin) {
        this._geolocationError = false;
        await super.onManualSelection(employeeId, enteredPin);
    },

    displayNotification(text) {
        if (this._geolocationError && text === _t("Wrong Pin")) {
            return;
        }
        super.displayNotification(text);
    },
});
