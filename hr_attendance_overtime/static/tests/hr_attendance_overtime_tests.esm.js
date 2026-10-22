/** @odoo-module **/
/**
 * Copyright 2025 Pierre Verkest
 * License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
 */
import {ActivityMenu} from "@hr_attendance/components/attendance_menu/attendance_menu";
import {patchWithCleanup} from "@web/../tests/helpers/utils";
import {session} from "@web/session";

// eslint-disable-next-line no-undef
QUnit.module("hr_attendance_overtime", function (hooks) {
    hooks.beforeEach(() => {
        console.log("setup test");
        this.activityMenuComponent = new ActivityMenu();
        patchWithCleanup(session.user_context, {tz: "Europe/Paris"});
    });
    // eslint-disable-next-line no-undef
    QUnit.test("test timeToStr paris", (assert) => {
        assert.expect(1);
        assert.strictEqual(
            this.activityMenuComponent.timeToStr("2021-07-23 15:13:36"),
            "16:13",
            "Should convert str datetime"
        );
    });

    // eslint-disable-next-line no-undef
    QUnit.test("test progressBarStyle", (assert) => {
        assert.expect(2);
        assert.strictEqual(
            this.activityMenuComponent.progressBarStyle(24),
            "width: 100%; font-size: 1.1em;",
            "Should compute all day attendance style"
        );
        assert.strictEqual(
            this.activityMenuComponent.progressBarStyle(12),
            "width: 50%; font-size: 1.1em;",
            "Should compute half day attendance style"
        );
    });
    // eslint-disable-next-line no-undef
    QUnit.test("test progressBarTheoreticalClass", (assert) => {
        assert.expect(2);
        assert.strictEqual(
            this.activityMenuComponent.progressBarTheoreticalClass({
                is_worktime: false,
            }),
            "progress-bar bg-light",
            "progressBarTheoreticalClass not working time"
        );
        assert.strictEqual(
            this.activityMenuComponent.progressBarTheoreticalClass({is_worktime: true}),
            "progress-bar bg-primary",
            "progressBarTheoreticalClass working time"
        );
    });
    // eslint-disable-next-line no-undef
    QUnit.test("test progressBarWorkedTimeTitle", (assert) => {
        assert.expect(2);
        assert.strictEqual(
            this.activityMenuComponent.progressBarWorkedTimeTitle({
                start: "2021-12-13 07:45:00",
                end: "2021-12-13 10:05:00",
                is_worktime: true,
            }),
            "08:45-11:05",
            "working time progressBarWorkedTimeTitle"
        );
        assert.strictEqual(
            this.activityMenuComponent.progressBarWorkedTimeTitle({
                start: "2021-12-13 07:45:00",
                end: "2021-12-13 10:05:00",
                is_worktime: false,
            }),
            "",
            "non working time progressBarWorkedTimeTitle"
        );
    });
    // eslint-disable-next-line no-undef
    QUnit.test("test progressBarWorkedTimeClass", (assert) => {
        assert.expect(3);
        assert.strictEqual(
            this.activityMenuComponent.progressBarWorkedTimeClass({is_worktime: false}),
            "progress-bar progress-bar-striped bg-light",
            "progressBarWorkedTimeClass break time"
        );
        assert.strictEqual(
            this.activityMenuComponent.progressBarWorkedTimeClass({
                is_worktime: true,
                is_checked_out: true,
            }),
            "progress-bar progress-bar-striped bg-success",
            "progressBarWorkedTimeClass working time checked out"
        );
        assert.strictEqual(
            this.activityMenuComponent.progressBarWorkedTimeClass({
                is_worktime: true,
                is_checked_out: false,
            }),
            "progress-bar progress-bar-striped bg-warning",
            "progressBarWorkedTimeClass working time not checked out"
        );
    });
});
