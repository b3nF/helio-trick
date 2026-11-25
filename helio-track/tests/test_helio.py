import numpy as np

from solartracker.controller import PID
from solartracker.simulation import TrackerConfig, simulate_day
from solartracker.sun import direct_normal_irradiance, panel_power, solar_position


def test_equinox_noon_elevation_matches_geometry():
    az, el = solar_position(41.0, 80, 12.0)
    assert abs(float(el) - 49.0) < 1.5      # 90 - latitude at the equinox
    assert abs(float(az) - 180.0) < 1.0     # due south


def test_sun_is_east_in_morning_west_in_afternoon():
    assert float(solar_position(41.0, 172, 8.0)[0]) < 180
    assert float(solar_position(41.0, 172, 16.0)[0]) > 180


def test_no_irradiance_below_horizon():
    assert direct_normal_irradiance(-5.0) == 0.0
    assert direct_normal_irradiance(60.0) > 800


def test_panel_facing_sun_beats_panel_facing_away():
    assert panel_power(180, 50, 180, 50) > 150
    assert panel_power(180, 50, 0, 10) < 1.0


def test_pid_converges_and_respects_limit():
    pid = PID(0.12, 0.0008, 0.0, out_limit=3.0, deadband=0.2)
    pos, target = 0.0, 40.0
    for _ in range(600):
        out = pid.update(target - pos, 1.0)
        assert abs(out) <= 3.0 + 1e-9
        pos += out
    assert abs(target - pos) < 0.5


def test_pid_deadband_gives_zero_output():
    assert PID(1.0, deadband=1.0).update(0.5, 1.0) == 0.0


def test_tracker_beats_fixed_panel_every_season():
    for day in (355, 80, 172, 266):
        r = simulate_day(41.0, day)
        assert r.energy_tracker_kwh > r.energy_fixed_kwh


def test_pointing_error_stays_small_while_tracking():
    r = simulate_day(41.0, 172, TrackerConfig())
    mid_day = (r.hours > 8) & (r.hours < 16)
    assert np.percentile(r.pointing_error[mid_day], 95) < 5.0
