/* Copyright 2021 Pierre Verkest
 * License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl). */
/* global QUnit*/
/* eslint no-undef: "error"*/

odoo.define("hr_attendance_overtime.tests", function (require) {
    "use strict";

    var testUtils = require("web.test_utils");
    var time = require("web.time");

    var MyAttendances = require("hr_attendance.my_attendances");
    QUnit.module(
        "HR-Attendance-Overtime",
        {
            beforeEach: function () {
                this.data = {
                    "hr.employee": {
                        fields: {
                            name: {string: "Name", type: "char"},
                            attendance_state: {
                                string: "State",
                                type: "selection",
                                selection: [
                                    ["checked_in", "In"],
                                    ["checked_out", "Out"],
                                ],
                                default: 1,
                            },
                            user_id: {string: "user ID", type: "integer"},
                            barcode: {string: "barcode", type: "integer"},
                            hours_today: {string: "Hours today", type: "float"},
                        },
                        records: [
                            {
                                id: 1,
                                name: "Employee A",
                                attendance_state: "checked_out",
                                user_id: 1,
                                barcode: 1,
                            },
                            {
                                id: 2,
                                name: "Employee B",
                                attendance_state: "checked_out",
                                user_id: 2,
                                barcode: 2,
                            },
                        ],
                        todays_working_times: {
                            done_attendances: [
                                {
                                    start: "2021-12-13 00:00:00",
                                    end: "2021-12-13 06:01:00",
                                    hours: 6.016666666666667,
                                    is_worktime: false,
                                },
                                {
                                    start: "2021-12-13 06:01:00",
                                    end: "2021-12-13 07:45:00",
                                    hours: 1.7333333333333334,
                                    is_checked_out: true,
                                    is_worktime: true,
                                },
                                {
                                    start: "2021-12-13 07:45:00",
                                    end: "2021-12-13 10:05:00",
                                    hours: 2.3333333333333335,
                                    is_checked_out: true,
                                    is_worktime: true,
                                },
                                {
                                    start: "2021-12-13 10:05:00",
                                    end: "2021-12-13 10:55:00",
                                    hours: 0.8333333333333334,
                                    is_checked_out: true,
                                    is_worktime: true,
                                },
                                {
                                    start: "2021-12-13 10:55:00",
                                    end: "2021-12-13 12:01:00",
                                    hours: 1.1,
                                    is_checked_out: true,
                                    is_worktime: true,
                                },
                                {
                                    start: "2021-12-13 12:01:00",
                                    end: "2021-12-13 14:11:00",
                                    hours: 2.1666666666666665,
                                    is_worktime: false,
                                },
                                {
                                    start: "2021-12-13 14:11:00",
                                    end: "2021-12-13 19:01:00",
                                    hours: 4.833333333333333,
                                    is_checked_out: false,
                                    is_worktime: true,
                                },
                            ],
                            message: "CHECK OUT MESSAGE",
                            state: "CHECK-OUT-LATE",
                            theoretical_work_times: [
                                {
                                    start: "2021-12-13 00:00:00",
                                    end: "2021-12-13 07:45:00",
                                    hours: 7.75,
                                    is_worktime: false,
                                },
                                {
                                    start: "2021-12-13 07:45:00",
                                    end: "2021-12-13 10:05:00",
                                    hours: 2.3333333333333335,
                                    is_worktime: true,
                                },
                                {
                                    start: "2021-12-13 10:05:00",
                                    end: "2021-12-13 10:55:00",
                                    hours: 0.8333333333333334,
                                    is_worktime: false,
                                },
                                {
                                    start: "2021-12-13 10:55:00",
                                    end: "2021-12-13 12:05:00",
                                    hours: 1.1666666666666667,
                                    is_worktime: true,
                                },
                                {
                                    start: "2021-12-13 12:05:00",
                                    end: "2021-12-13 12:55:00",
                                    hours: 0.8333333333333334,
                                    is_worktime: false,
                                },
                                {
                                    start: "2021-12-13 12:55:00",
                                    end: "2021-12-13 17:05:00",
                                    hours: 4.166666666666667,
                                    is_worktime: true,
                                },
                            ],
                        },
                    },
                    "res.company": {
                        fields: {
                            name: {string: "Name", type: "char"},
                        },
                        records: [
                            {
                                id: 1,
                                name: "Company A",
                            },
                        ],
                    },
                };
            },
        },
        function () {
            QUnit.test("test signOutExtraClass", function (assert) {
                assert.expect(2);
                var clientAction = new MyAttendances(null, {});
                clientAction.overtime_info = {state: "UNKNOWN"};
                assert.strictEqual(
                    clientAction.signOutExtraClass(),
                    "btn-danger",
                    "Unknown state return danger"
                );
                clientAction.overtime_info.state = "CHECK-OUT-ONTIME";
                assert.strictEqual(
                    clientAction.signOutExtraClass(),
                    "btn-info",
                    "CHECK-OUT-ONTIME state return btn-info"
                );
            });
            QUnit.test("test signInExtraClass", function (assert) {
                assert.expect(2);
                var clientAction = new MyAttendances(null, {});
                clientAction.overtime_info = {state: "UNKNOWN"};
                assert.strictEqual(
                    clientAction.signInExtraClass(),
                    "btn-danger",
                    "Unknown state return danger"
                );
                clientAction.overtime_info.state = "CHECK-IN-ONTIME";
                assert.strictEqual(
                    clientAction.signInExtraClass(),
                    "btn-success",
                    "CHECK-IN-ONTIME state return btn-info"
                );
            });
            QUnit.test("test timeToStr", function (assert) {
                assert.expect(2);
                var clientAction = new MyAttendances(null, {});
                clientAction.format_time = time.strftime_to_moment_format(
                    "%H hours and %M minutes"
                );
                // TODO not sure how tu force moment browser timezone
                // methods call `.local()` which I supposed to be
                // browser dependant
                assert.strictEqual(
                    clientAction.timeToStr("2021-12-23 15:13:36"),
                    "16 hours and 13 minutes",
                    "Should convert str datetime"
                );
                assert.strictEqual(
                    clientAction.timeToStr("2021-12-23 15:13:36", "%HoOo%M"),
                    "16oOo13",
                    "Should convert str datetime"
                );
            });
            QUnit.test("test progressBarStyle", function (assert) {
                assert.expect(2);
                var clientAction = new MyAttendances(null, {});
                assert.strictEqual(
                    clientAction.progressBarStyle(24),
                    "width: 100%; font-size: 1.1em;",
                    "Should compute all day attendance style"
                );
                assert.strictEqual(
                    clientAction.progressBarStyle(12),
                    "width: 50%; font-size: 1.1em;",
                    "Should compute half day attendance style"
                );
            });
            QUnit.test("test progressBarTheoreticalClass", function (assert) {
                assert.expect(2);
                var clientAction = new MyAttendances(null, {});
                assert.strictEqual(
                    clientAction.progressBarTheoreticalClass({is_worktime: false}),
                    "progress-bar bg-light",
                    "progressBarTheoreticalClass not working time"
                );
                assert.strictEqual(
                    clientAction.progressBarTheoreticalClass({is_worktime: true}),
                    "progress-bar bg-primary",
                    "progressBarTheoreticalClass working time"
                );
            });
            QUnit.test("test progressBarWorkedTimeClass", function (assert) {
                assert.expect(3);
                var clientAction = new MyAttendances(null, {});
                assert.strictEqual(
                    clientAction.progressBarWorkedTimeClass({is_worktime: false}),
                    "progress-bar progress-bar-striped bg-light",
                    "progressBarWorkedTimeClass break time"
                );
                assert.strictEqual(
                    clientAction.progressBarWorkedTimeClass({
                        is_worktime: true,
                        is_checked_out: true,
                    }),
                    "progress-bar progress-bar-striped bg-success",
                    "progressBarWorkedTimeClass working time checked out"
                );
                assert.strictEqual(
                    clientAction.progressBarWorkedTimeClass({
                        is_worktime: true,
                        is_checked_out: false,
                    }),
                    "progress-bar progress-bar-striped bg-warning",
                    "progressBarWorkedTimeClass working time not checked out"
                );
            });
            QUnit.test("Rendering overtime informations", async function (assert) {
                assert.expect(2);

                var rpcCount = 0;
                var self = this;
                var $target = $("#qunit-fixture");
                var clientAction = new MyAttendances(null, {});
                await testUtils.mock.addMockEnvironment(clientAction, {
                    data: this.data,
                    session: {
                        uid: 1,
                    },
                    mockRPC: function (route, args) {
                        if (
                            args.method === "todays_working_times" &&
                            args.model === "hr.employee"
                        ) {
                            rpcCount++;
                            return Promise.resolve(
                                self.data["hr.employee"].todays_working_times
                            );
                        }
                        return this._super(route, args);
                    },
                });
                await clientAction.appendTo($target);
                assert.strictEqual(
                    rpcCount,
                    1,
                    "RPC call should have been done only once."
                );

                assert.strictEqual(
                    clientAction
                        .$(
                            ".o_hr_attendance_kiosk_mode h3.o_hr_attendance_overtime_message"
                        )
                        .text(),
                    "CHECK OUT MESSAGE",
                    "should have rendered the checking reason"
                );

                clientAction.destroy();
            });
        }
    );
});
