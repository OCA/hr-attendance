* Ensure employee weeks are properly set
* Set `is_compensatory` on leave types to:
  * reduce domain to select leave type in hr configuration
  * to dispatch taken leaves on validation sheet
* Set the leave type to use by generating compensatory
  hours from attendance review (to be done in hr attendance configuration).
  We use to create a new type `hr.leave.type` manually each years.
* You can ignore some leaves in validation sheet by ticking the
  "Ignored in attendance validation" on holidays `hr.leave.type``
  (for instance it can be useful if you manage employee remote days using hr.leave
  in such case you want to ignore those lines)
* configure public holidays to take care of it while computing the theoretical week time
* once all leaves and attendances has been recorded you can generate leave reviews
  by setting up a cron job running every monday morning to generate the previous week
  with the following code on `hr.attendance.validation.sheet` model::

    model.generate_reviews()
