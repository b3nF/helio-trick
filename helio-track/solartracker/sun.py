"""Solar geometry and a simple clear-sky irradiance model."""
from __future__ import annotations

import numpy as np


def solar_position(lat_deg: float, day_of_year: int, hour):
    """Return (azimuth, elevation) in degrees.

    Azimuth is measured clockwise from north (east=90, south=180, west=270).
    Uses Cooper's declination formula and local solar time (hour 0-24).
    """
    hour = np.asarray(hour, dtype=float)
    lat = np.radians(lat_deg)
    decl = np.radians(23.45) * np.sin(np.radians(360.0 / 365.0 * (284 + day_of_year)))
    ha = np.radians(15.0 * (hour - 12.0))
    sin_el = np.sin(lat) * np.sin(decl) + np.cos(lat) * np.cos(decl) * np.cos(ha)
    el = np.arcsin(np.clip(sin_el, -1.0, 1.0))
    cos_az = (np.sin(decl) - np.sin(el) * np.sin(lat)) / (np.cos(el) * np.cos(lat) + 1e-12)
    az = np.arccos(np.clip(cos_az, -1.0, 1.0))
    az = np.where(ha > 0, 2 * np.pi - az, az)
    return np.degrees(az), np.degrees(el)


def unit_vector(az_deg, el_deg):
    """East-North-Up unit vector for an azimuth/elevation pair."""
    az, el = np.radians(az_deg), np.radians(el_deg)
    return np.array([np.cos(el) * np.sin(az), np.cos(el) * np.cos(az), np.sin(el)])


def direct_normal_irradiance(el_deg: float) -> float:
    """Clear-sky direct normal irradiance in W/m^2 (Meinel model)."""
    if el_deg <= 1.0:
        return 0.0
    air_mass = 1.0 / np.sin(np.radians(el_deg))
    return float(1353.0 * 0.7 ** (air_mass ** 0.678))


def panel_power(sun_az, sun_el, panel_az, panel_el, area=1.0, efficiency=0.20) -> float:
    """Electrical power (W) from direct irradiance on a panel.

    panel_el is the elevation of the panel normal (90 = facing straight up).
    """
    dni = direct_normal_irradiance(sun_el)
    if dni == 0.0:
        return 0.0
    cos_inc = float(np.dot(unit_vector(sun_az, sun_el), unit_vector(panel_az, panel_el)))
    return dni * max(0.0, cos_inc) * area * efficiency
