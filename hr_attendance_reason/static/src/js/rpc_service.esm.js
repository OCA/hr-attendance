/** @odoo-module */
import {rpcService} from "@web/core/network/rpc_service";

// Patch the function start to capture rpc call
// and add to params the attendance_reason_id if exists
const originalStart = rpcService.start;
rpcService.start = function (env) {
    const originalRpc = originalStart(env);
    return function rpc(route, params = {}, settings = {}) {
        if (
            (route === "/hr_attendance/systray_check_in_out" ||
                route === "manual_selection") &&
            $("#attendance_reason").length
        ) {
            if ($("#attendance_reason").val() !== "0") {
                params.attendance_reason_id = $("#attendance_reason").val();
            }
        }
        // Call original function
        return originalRpc(route, params, settings);
    };
};
