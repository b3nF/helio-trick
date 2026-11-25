"""Command line: python -m solartracker --lat 41.0 --plot"""
from __future__ import annotations

import argparse
from pathlib import Path

from .simulation import TrackerConfig, simulate_day

SEASONS = {"Winter solstice": 355, "Spring equinox": 80, "Summer solstice": 172, "Autumn equinox": 266}


def main() -> None:
    ap = argparse.ArgumentParser(description="Fixed panel vs dual-axis tracker simulation")
    ap.add_argument("--lat", type=float, default=41.0, help="latitude in degrees (default: Istanbul)")
    ap.add_argument("--noise", type=float, default=0.5, help="sensor noise, degrees")
    ap.add_argument("--plot", action="store_true", help="save plots to results/")
    ap.add_argument("--out", default="results")
    args = ap.parse_args()

    cfg = TrackerConfig(sensor_noise=args.noise)
    results = {name: simulate_day(args.lat, d, cfg) for name, d in SEASONS.items()}

    print(f"Latitude {args.lat} deg | per 1 m2 panel, 20% efficiency, clear sky, direct beam")
    print(f"{'Day':<18}{'Fixed kWh':>11}{'Tracker kWh':>13}{'Gain':>9}")
    for name, r in results.items():
        print(f"{name:<18}{r.energy_fixed_kwh:>11.2f}{r.energy_tracker_kwh:>13.2f}{r.gain_percent:>8.1f}%")

    if args.plot:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        out = Path(args.out)
        out.mkdir(exist_ok=True)
        r = results["Summer solstice"]
        fig, axes = plt.subplots(1, 2, figsize=(12, 4.2))
        axes[0].plot(r.hours, r.power_fixed, label="Fixed (south, tilt = latitude)")
        axes[0].plot(r.hours, r.power_tracker, label="Dual-axis PID tracker")
        axes[0].set(title="Power output, summer solstice", xlabel="Solar time (h)",
                    ylabel="W per m2", xlim=(4, 20))
        axes[0].legend()
        axes[0].grid(alpha=0.3)
        names = list(results)
        x = list(range(len(names)))
        axes[1].bar([i - 0.2 for i in x], [results[n].energy_fixed_kwh for n in names], 0.4, label="Fixed")
        axes[1].bar([i + 0.2 for i in x], [results[n].energy_tracker_kwh for n in names], 0.4, label="Tracker")
        axes[1].set_xticks(x)
        axes[1].set_xticklabels(names, rotation=15)
        axes[1].set(title="Daily energy by season", ylabel="kWh per m2 per day")
        axes[1].legend()
        fig.tight_layout()
        fig.savefig(out / "comparison.png", dpi=150)

        fig2, ax = plt.subplots(figsize=(7, 3.8))
        ax.plot(r.hours, r.pointing_error)
        ax.set(title="Pointing error (summer solstice)", xlabel="Solar time (h)",
               ylabel="degrees", xlim=(4, 20), ylim=(0, 15))
        ax.grid(alpha=0.3)
        fig2.tight_layout()
        fig2.savefig(out / "pointing_error.png", dpi=150)
        print(f"Plots saved to {out}/")


if __name__ == "__main__":
    main()
