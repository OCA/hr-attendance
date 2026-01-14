Not fully compatible with hr_attendance_geolocation. Sign-out
coordinates are stored in the main attendance record when signing out
rest time. In upper versions with geolocation, we need to review
compatibility.

Also not fully compatible with hr_attendance_modification_tracking.
Tracking not working correctly for the model hr_attendance_rest_time. In
upper odoo version tracking is part of core, we need to review.
