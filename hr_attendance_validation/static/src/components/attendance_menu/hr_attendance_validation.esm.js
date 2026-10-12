/* @odoo-module */
/**
 * Copyright 2025 Pierre Verkest
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
 */
import {ActivityMenu} from "@hr_attendance/components/attendance_menu/attendance_menu";
import {patch} from "@web/core/utils/patch";

patch(ActivityMenu.prototype, {
    async searchReadEmployee() {
        await super.searchReadEmployee(...arguments);
        if (this.employee.id) {
            this.hoursWeek = this.date_formatter(this.employee.hours_current_week);
        }
    },
});
