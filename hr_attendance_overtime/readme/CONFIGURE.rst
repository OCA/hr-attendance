This modules depend on different configurations:

To setup ranges hours on employee work time weeks:

#. Go to *Settings > Technical > Resource > Working Times*
   or from employee form Go to *Employees > Employees > in employee form view > working hours*.
#. On the form view you can setup 4 new fields add by this module on each attendance lines

  * *check-in from*: Check-in before will result an extra overtime line with an earlier check-in reason (`CI-E`)
  * *check-in to*: Check-in after will add a late check-in reason (`CI-L`)
  * *check-out from*: Check-out before will add a earlier check-out reason (`CO-E`)
  * *check-out to*: Check-out after will generate an extra overtime line with a late check-out reason (`CO-L`)

We have chosen to not reuse existing *Work from* and *Work to* that are used by other modules like *hr_holidays*
with compensatoires leaves. To be able to define a bigger range that overlap that time.

You can personalize 4 kinds of reason label that are selected by code which must remains the same and uniq:

#. Go to *Attendances > configuration > Reason*
#. personalize name for following code:

  * `CI-E`: check-in earlier (checked-in occurred before *check-in from*)
  * `CI-L`: check-in late (checked-in occurred after *check-in to*)
  * `CO-E`: check-out earlier (checked-out occurred before *check-out from*)
  * `CO-L`: check-out late (checked-out occurred after *check-out to*)
