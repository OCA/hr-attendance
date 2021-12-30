* Ensure employee weeks are properly set
* Set the leave type to use by generating compensatory
  hours from attendance review (to be done in hr attendance configuration)
* once all leaves and attendances has been recorded you can generate leave reviews
  by setting up a cron job running every monday morning to generate the previous week
  with the following code on `hr.attendance.validation.sheet` model::

    model.generate_reviews()
