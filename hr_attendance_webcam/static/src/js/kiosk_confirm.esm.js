/** @odoo-module **/
/* global Webcam */

import KioskConfirm from "hr_attendance.kiosk_confirm";
import Session from "web.session";

KioskConfirm.include({
    events: _.extend({}, KioskConfirm.prototype.events, {
        "click .o_hr_attendance_sign_in_out_icon": _.debounce(
            function () {
                if (this.has_group_webcam) {
                    Webcam.attach(".o_hr_attendance_webcam");
                    this.is_button_ok = false;
                    $(".o_modal_camera_attendance").modal("show");
                    setTimeout(function () {
                        self.$(".o_hr_confirm_dialog_button").removeAttr("disabled");
                    }, 500);
                } else {
                    this.update_attendance();
                }
            },
            200,
            true
        ),
        "click .o_hr_attendance_pin_pad_button_ok": _.debounce(
            function () {
                if (this.has_group_webcam) {
                    Webcam.attach(".o_hr_attendance_webcam");
                    this.is_button_ok = true;
                    $(".o_modal_camera_attendance").modal("show");
                    setTimeout(function () {
                        self.$(".o_hr_confirm_dialog_button").removeAttr("disabled");
                    }, 500);
                } else {
                    this._send_pin_debounced();
                }
            },
            200,
            true
        ),
        "click .o_hr_confirm_dialog_button": function () {
            if (this.is_button_ok) {
                this._send_pin_debounced();
            } else {
                this.update_attendance();
            }
            $(".o_modal_camera_attendance").modal("hide");
            $(".o_hr_confirm_dialog_button").attr("disabled", "disabled");
        },
        "click .o_hr_cancel_dialog_button": function () {
            if (Webcam.live) Webcam.reset();
            $(".o_modal_camera_attendance").modal("hide");
            $(".o_hr_confirm_dialog_button").attr("disabled", "disabled");
        },
    }),

    init: function () {
        this._super.apply(this, ...arguments);
        this.image = null;
        this.has_group_webcam = false;
    },

    start: function () {
        this._super.apply(this, arguments);
        var self = this;
        this.getSession()
            .user_has_group("hr_attendance_webcam.group_hr_attendance_image_capture")
            .then((has_group) => {
                if (has_group) {
                    self.has_group_webcam = true;
                    Webcam.set({
                        width: 720,
                        height: 320,
                        image_format: "jpeg",
                        jpeg_quality: 90,
                        force_flash: false,
                        flip_horiz: false,
                        fps: 45,
                        swfURL: "/hr_attendance_webcam/static/src/lib/webcam/webcam.swf",
                    });
                }
            });
    },

    update_attendance: function () {
        var self = this;
        if (Webcam.live) {
            Webcam.snap(function (data_uri) {
                self.image = data_uri.split(",")[1];
            });
            Webcam.reset();
        }
        const ctx = Object.assign(Session.user_context, {image: this.image});
        this._rpc({
            model: "hr.employee",
            method: "attendance_manual",
            args: [[self.employee_id], this.next_action],
            context: ctx,
        }).then(function (result) {
            if (result.action) {
                self.do_action(result.action);
            } else if (result.warning) {
                self.displayNotification({title: result.warning, type: "danger"});
            }
        });
    },

    _sendPin: function () {
        var self = this;
        if (Webcam.live) {
            Webcam.snap(function (data_uri) {
                self.image = data_uri.split(",")[1];
            });
            Webcam.reset();
        }
        const ctx = Object.assign(Session.user_context, {image: this.image});
        this.$(".o_hr_attendance_pin_pad_button_ok").attr("disabled", "disabled");
        this._rpc({
            model: "hr.employee",
            method: "attendance_manual",
            args: [
                [this.employee_id],
                this.next_action,
                this.$(".o_hr_attendance_PINbox").val(),
            ],
            context: ctx,
        }).then(function (result) {
            self.pin_is_send = true;
            if (result.action) {
                self.do_action(result.action);
            } else if (result.warning) {
                self.displayNotification({title: result.warning, type: "danger"});
                self.$(".o_hr_attendance_PINbox").val("");
                setTimeout(function () {
                    self.$(".o_hr_attendance_pin_pad_button_ok").removeAttr("disabled");
                }, 500);
            }
        });
    },

    destroy: function () {
        if (Webcam.live) Webcam.reset();
        this._super.apply(this, arguments);
    },
});
