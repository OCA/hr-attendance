/* @odoo-module */
/**
 * Copyright 2025 Pierre Verkest
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
 */
import {ActivityMenu} from "@hr_attendance/components/attendance_menu/attendance_menu";
import {formatDateTime} from "@web/core/l10n/dates";
import {patch} from "@web/core/utils/patch";
import {session} from "@web/session";

const {DateTime} = luxon;

patch(ActivityMenu.prototype, {
    async searchReadEmployee() {
        await super.searchReadEmployee(...arguments);
        if (this.employee.id && this.employee.overtime_info) {
            this.overtimeInfo = this.employee.overtime_info;
        }
    },
    timeToStr(utc_str_datetime) {
        const userTz = session.user_context.tz || luxon.Settings.defaultZoneName;
        console.log(session.user_context.tz);
        const utc_dt = DateTime.fromFormat(utc_str_datetime, "yyyy-MM-dd HH:mm:ss", {
            zone: "utc",
        });
        const tz_time = formatDateTime(utc_dt.setZone(userTz), {format: "HH':'mm"});
        return tz_time;
    },
    progressBarStyle(hours) {
        return `width: ${(hours / 24) * 100}%; font-size: 1.1em;`;
    },
    progressBarTheoreticalClass(worktime) {
        const baseClass = "progress-bar ";
        if (worktime.is_worktime === true) {
            return baseClass + "bg-primary";
        }
        return baseClass + "bg-light";
    },
    progressBarWorkedTimeTitle(worktime) {
        let title = "";
        if (worktime.is_worktime === true) {
            title = `${this.timeToStr(worktime.start)}-${this.timeToStr(worktime.end)}`;
        }
        return title;
    },
    progressBarWorkedTimeClass(worktime) {
        const baseClass = "progress-bar progress-bar-striped ";
        if (worktime.is_worktime === true) {
            return baseClass + (worktime.is_checked_out ? "bg-success" : "bg-warning");
        }
        return baseClass + "bg-light";
    },
});
