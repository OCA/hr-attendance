# Copyright 2026 Binhex Systems Solutions S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging

from odoo import tools

from .service_map import PROVIDER_MAP

_logger = logging.getLogger(__name__)


class GeocodingService:
    """
    Main reverse geocoding service.

    Orchestrates:
    - Coordinate normalization
    - Cache lookup (hr.attendance.geocode.cache)
    - Call to configured external provider
    - Result persistence in cache

    Has no own state; receives the Odoo environment (env) in each operation.
    """

    def __init__(self, env):
        self.env = env
        self.dp = self._get_rounding_precision()
        self.latitude_normalize = None
        self.longtide_normalize = None

    def get_address(self, latitude, longitude):
        """
        Get address for the given coordinates.

        Flow:
        1. Normalize coordinates according to configured precision
        2. Search in cache
        3. If no cache → call external provider
        4. Persist in cache if new result

        :param latitude: float
        :param longitude: float
        :return: dict {address, map_url, provider, from_cache}
        :raises: Exception if provider fails and no cache available
        """
        self.latitude_normalize = tools.float_round(latitude, precision_digits=self.dp)
        self.longtide_normalize = tools.float_round(longitude, precision_digits=self.dp)

        provider_key = self._get_provider_key()

        cached = self._lookup_cache(
            self.latitude_normalize, self.longtide_normalize, provider_key
        )
        if cached:
            return {
                "address": cached.address,
                "map_url": cached.map_url,
                "provider": cached.provider,
            }

        provider = self._build_provider(provider_key)
        result = provider.reverse_geocode(
            self.latitude_normalize, self.longtide_normalize
        )

        self._save_cache(self.latitude_normalize, self.longtide_normalize, result)

        result["from_cache"] = False
        return result

    def _get_rounding_precision(self):
        param = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(
                "hr_attendance_reverse_geocoding.rounding_precision",
            )
        )
        return int(param)

    def _get_provider_key(self):
        return (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(
                "hr_attendance_reverse_geocoding.provider",
                default="mapbox",
            )
        )

    def _get_api_key(self):
        return (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(
                "hr_attendance_reverse_geocoding.api_key",
                default="",
            )
        )

    def _get_endpoint(self):
        return (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(
                "hr_attendance_reverse_geocoding.endpoint",
                default="",
            )
        )

    def _build_provider(self, provider_key):
        """Instantiate external provider according to configuration."""
        Provider = PROVIDER_MAP.get(provider_key)
        if not Provider:
            raise ValueError(
                f"Provider not found: '{provider_key}'. "
                f"Available providers: {list(PROVIDER_MAP.keys())}"
            )
        api_key = self._get_api_key()
        endpoint = self._get_endpoint() or None
        return Provider(api_key=api_key, endpoint=endpoint)

    def _lookup_cache(self, latitude_normalize, longtide_normalize, provider_key):
        """Search in cache by normalized coordinates and provider."""
        return (
            self.env["hr.attendance.geocode.cache"]
            .sudo()
            .search(
                [
                    ("latitude_normalize", "=", latitude_normalize),
                    ("longtide_normalize", "=", longtide_normalize),
                    ("provider", "=", provider_key),
                ],
                limit=1,
            )
        )

    def _save_cache(self, latitude_normalize, longtide_normalize, result):
        """Persist result in cache or update if already exists."""
        Cache = self.env["hr.attendance.geocode.cache"].sudo()
        existing = Cache.search(
            [
                ("latitude_normalize", "=", latitude_normalize),
                ("longtide_normalize", "=", longtide_normalize),
                ("provider", "=", result["provider"]),
            ],
            limit=1,
        )
        vals = {
            "address": result["address"],
            "map_url": result.get("map_url", ""),
        }
        if existing:
            existing.write(vals)
        else:
            Cache.create(
                {
                    "latitude_normalize": latitude_normalize,
                    "longtide_normalize": longtide_normalize,
                    "provider": result["provider"],
                    **vals,
                }
            )
