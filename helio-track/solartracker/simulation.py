"""Time-domain simulation: fixed panel vs. dual-axis PID tracker."""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .controller import PID
from .sun import panel_power, solar_position

AZ_LIMITS = (45.0, 315.0)   # mechanical range of the azimuth axis (deg)
EL_LIMITS = (5.0, 90.0)     # mechanical range of the elevation axis (deg)
PARK = (90.0, 10.0)         # night position: face the sunrise


@dataclass
class TrackerConfig:
    kp: float = 0.12
    ki: float = 0.0008
    kd: float = 0.0
    max_rate: float = 3.0        # deg/s, servo + gearbox speed limit
    deadband: float = 1.0        # deg, avoids jitter and saves energy
    sensor_noise: float = 0.5    # deg, 1-sigma noise of the light sensor
    dt: float = 5.0              # s, control period
    seed: int = 42


@dataclass
class DayResult:
    hours: np.ndarray
    power_fixed: np.ndarray
    power_tracker: np.ndarray
    az_cmd: np.ndarray
    el_cmd: np.ndarray
    pointing_error: np.ndarray
    energy_fixed_kwh: float = 0.0
    energy_tracker_kwh: float = 0.0
    gain_percent: float = field(init=False)

    def __post_init__(self):
        self.gain_percent = 100.0 * (self.energy_tracker_kwh / self.energy_fixed_kwh - 1.0)


def _wrap(angle: float) -> float:
    return (angle + 180.0) % 360.0 - 180.0


def simulate_day(lat: float, day: int, cfg: TrackerConfig | None = None,
                 fixed_tilt: float | None = None) -> DayResult:
    """Simulate one day. The fixed panel faces south at a tilt equal to latitude by default."""
    cfg = cfg or TrackerConfig()
    rng = np.random.default_rng(cfg.seed)
    tilt = lat if fixed_tilt is None else fixed_tilt
    fixed_az, fixed_el = 180.0, 90.0 - tilt

    pid_az = PID(cfg.kp, cfg.ki, cfg.kd, out_limit=cfg.max_rate, deadband=cfg.deadband)
    pid_el = PID(cfg.kp, cfg.ki, cfg.kd, out_limit=cfg.max_rate, deadband=cfg.deadband)
    az, el = PARK

    n = int(24 * 3600 / cfg.dt)
    hours = np.arange(n) * cfg.dt / 3600.0
    p_fixed, p_track = np.zeros(n), np.zeros(n)
    az_log, el_log, err_log = np.zeros(n), np.zeros(n), np.zeros(n)

    for i, h in enumerate(hours):
        s_az, s_el = solar_position(lat, day, h)
        s_az, s_el = float(s_az), float(s_el)
        if s_el > 2.0:  # sun visible: closed-loop tracking on a noisy sensor error
            e_az = _wrap(s_az - az) + rng.normal(0, cfg.sensor_noise)
            e_el = (s_el - el) + rng.normal(0, cfg.sensor_noise)
            az += pid_az.update(e_az, cfg.dt) * cfg.dt
            el += pid_el.update(e_el, cfg.dt) * cfg.dt
        else:           # night: slew back to the park position
            pid_az.reset()
            pid_el.reset()
            az += np.clip(PARK[0] - az, -cfg.max_rate * cfg.dt, cfg.max_rate * cfg.dt)
            el += np.clip(PARK[1] - el, -cfg.max_rate * cfg.dt, cfg.max_rate * cfg.dt)
        az = float(np.clip(az, *AZ_LIMITS))
        el = float(np.clip(el, *EL_LIMITS))

        p_fixed[i] = panel_power(s_az, s_el, fixed_az, fixed_el)
        p_track[i] = panel_power(s_az, s_el, az, el)
        az_log[i], el_log[i] = az, el
        if s_el > 2.0:
            c = (np.cos(np.radians(s_el)) * np.cos(np.radians(el)) * np.cos(np.radians(s_az - az))
                 + np.sin(np.radians(s_el)) * np.sin(np.radians(el)))
            err_log[i] = np.degrees(np.arccos(np.clip(c, -1, 1)))

    to_kwh = cfg.dt / 3600.0 / 1000.0
    return DayResult(hours, p_fixed, p_track, az_log, el_log, err_log,
                     float(p_fixed.sum() * to_kwh), float(p_track.sum() * to_kwh))
