from functools import lru_cache

import pycountry
import reverse_geocoder as rg


@lru_cache(maxsize=8192)
def region_label(lat_rounded: float, lng_rounded: float) -> str:
    """Return human-readable region label for rounded lat/lng."""
    try:
        results = rg.search([(lat_rounded, lng_rounded)])
        row = results[0]
    except Exception:
        return f"{lat_rounded}, {lng_rounded}"

    cc = (row.get("cc") or "").upper()
    admin1 = (row.get("admin1") or "").strip()

    try:
        country = pycountry.countries.get(alpha_2=cc)
        country_name = country.name if country else cc
    except Exception:
        country_name = cc

    if admin1 and admin1 not in ("", "NA", "N/A"):
        return f"{country_name} — {admin1}"
    return country_name


def region_for_packet(latitude: float, longitude: float) -> str:
    lat_r = round(float(latitude), 2)
    lng_r = round(float(longitude), 2)
    return region_label(lat_r, lng_r)
