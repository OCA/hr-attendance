/* @odoo-module */

import {ActivityMenu} from "@hr_attendance/components/attendance_menu/attendance_menu";
import {browser} from "@web/core/browser/browser";
import {isIosApp} from "@web/core/browser/feature_detection";
import {patch} from "@web/core/utils/patch";
import publicKioskAppModule from "@hr_attendance/public_kiosk/public_kiosk_app";
import {rpc} from "@web/core/network/rpc";

const {kioskAttendanceApp} = publicKioskAppModule;

patch(ActivityMenu.prototype, {
    async signInOut() {
        this.dropdown.close();

        const checkInOut = async (latitude, longitude) => {
            await rpc("/hr_attendance/systray_check_in_out", {latitude, longitude});
            await this.searchReadEmployee();
        };

        if (isIosApp() || !browser.navigator.geolocation) {
            await checkInOut(0.0, 0.0);
            return;
        }

        await new Promise((resolve) => {
            browser.navigator.geolocation.getCurrentPosition(
                async ({coords: {latitude, longitude}}) => {
                    await checkInOut(latitude, longitude);
                    resolve();
                },
                async () => {
                    await checkInOut(0.0, 0.0);
                    resolve();
                },
                {
                    enableHighAccuracy: true,
                }
            );
        });
    },
});

if (kioskAttendanceApp) {
    patch(kioskAttendanceApp.prototype, {
        async makeRpcWithGeolocation(route, params) {
            if (isIosApp() || !browser.navigator.geolocation) {
                return rpc(route, {
                    ...params,
                    latitude: 0.0,
                    longitude: 0.0,
                });
            }

            return new Promise((resolve) => {
                browser.navigator.geolocation.getCurrentPosition(
                    async ({coords: {latitude, longitude}}) => {
                        const result = await rpc(route, {
                            ...params,
                            latitude,
                            longitude,
                        });
                        resolve(result);
                    },
                    async () => {
                        const result = await rpc(route, {
                            ...params,
                            latitude: 0.0,
                            longitude: 0.0,
                        });
                        resolve(result);
                    },
                    {
                        enableHighAccuracy: true,
                    }
                );
            });
        },
    });
}
