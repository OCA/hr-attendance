Go to **Attendances > Configuration > Settings** and configure:

1. **Geocoding Provider**: select Mapbox
2. **API Key**: enter your Mapbox API key
3. **Rounding Precision**: number of decimal places for cache (default: 4)

For Mapbox, get your API key at https://account.mapbox.com/

The module works transparently:

1. Employee checks in/out with geolocation active
2. System automatically queues a reverse geocoding job
3. Worker processes the job and updates the address in the attendance record
4. Address is visible in the "Geocode" tab of the form

Possible states are:

- **Pending**: job is queued and waiting to be processed
- **Done**: address has been obtained successfully
- **Error**: failed (visible in logs for administrators)

Adding new providers
====================

To integrate a new provider:

1. Create ``services/providers/my_provider.py`` inheriting from ``BaseGeocodingProvider``
2. Implement the ``reverse_geocode(latitude, longitude)`` method
3. Register in ``PROVIDER_MAP`` of ``services/service_map.py``
4. Add the option in ``PROVIDER_SELECTION`` of ``models/res_config_settings.py``
