"""
Offline GeoIP enrichment service.
Uses local MaxMind GeoLite2 MMDB file via geoip2.
Implements graceful fallback:
If MMDB file is absent or lookup fails, returns null fields without pipeline crash.
Adheres to strict offline forensics principles: geolocations are labeled as approximate.
"""
import os
from typing import Dict, Any, Optional
from backend.app.core.config import settings

try:
    import geoip2.database
    import geoip2.errors
    GEOIP2_AVAILABLE = True
except ImportError:
    GEOIP2_AVAILABLE = False


class GeoIPService:
    """
    Offline local GeoIP reader with fallback.
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or settings.GEOIP_DATABASE_PATH
        self._reader = None
        self._status = "unavailable"
        self._init_reader()

    def _init_reader(self):
        if not GEOIP2_AVAILABLE:
            self._status = "library_missing"
            return

        if self.db_path and os.path.exists(self.db_path):
            try:
                self._reader = geoip2.database.Reader(self.db_path)
                self._status = "available"
            except Exception:
                self._reader = None
                self._status = "error_loading_db"
        else:
            self._status = "db_not_found"

    @property
    def status(self) -> str:
        return self._status

    def lookup(self, ip_address: Optional[str]) -> Dict[str, Any]:
        """
        Enriches an IP address with approximate location metadata.
        Returns dict with keys:
            country (ISO code or None),
            region (None or name),
            city (None or name),
            asn (None or number/name),
            geo_source (str),
            geo_status (str),
            disclaimer (str)
        """
        result: Dict[str, Any] = {
            "country": None,
            "region": None,
            "city": None,
            "asn": None,
            "geo_source": "GeoLite2-City" if self._status == "available" else None,
            "geo_status": self._status,
            "disclaimer": "Observed IP was geolocated approximately by local GeoIP database. Not person-level attribution."
        }

        if not ip_address or self._reader is None:
            return result

        clean_ip = ip_address.strip()
        try:
            response = self._reader.city(clean_ip)
            if response.country and response.country.iso_code:
                result["country"] = response.country.iso_code
            if response.subdivisions and len(response.subdivisions) > 0:
                result["region"] = response.subdivisions[0].name
            if response.city and response.city.name:
                result["city"] = response.city.name
            result["geo_status"] = "enriched"
        except (geoip2.errors.AddressNotFoundError, ValueError):
            result["geo_status"] = "not_found"
        except Exception as e:
            result["geo_status"] = f"lookup_error: {str(e)}"

        return result

    def close(self):
        if self._reader:
            try:
                self._reader.close()
            except Exception:
                pass
            self._reader = None


geoip_service = GeoIPService()
