def migrate(cr, version):
    """Existing devices keep the previous behaviour.

    Before this version the module stored the appliance wall-clock time as
    if it were UTC. Defaulting existing devices to UTC keeps their data
    interpretation unchanged; administrators whose appliance reports local
    time must set the real timezone on the device and shift the already
    stored events themselves.
    """
    cr.execute(
        """
        ALTER TABLE idsecure_device ADD COLUMN IF NOT EXISTS tz VARCHAR;
        UPDATE idsecure_device SET tz = 'UTC' WHERE tz IS NULL;
        """
    )
