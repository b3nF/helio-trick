"""PID controller with anti-windup, output saturation and a deadband."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PID:
    kp: float
    ki: float = 0.0
    kd: float = 0.0
    out_limit: float = float("inf")
    deadband: float = 0.0
    _integral: float = 0.0
    _prev_error: float | None = None

    def reset(self) -> None:
        self._integral = 0.0
        self._prev_error = None

    def update(self, error: float, dt: float) -> float:
        if abs(error) < self.deadband:
            self._prev_error = error
            self._integral *= 0.9  # bleed the integrator inside the deadband
            return 0.0
        deriv = 0.0 if self._prev_error is None else (error - self._prev_error) / dt
        self._prev_error = error
        candidate = self._integral + error * dt
        out = self.kp * error + self.ki * candidate + self.kd * deriv
        if abs(out) <= self.out_limit:  # anti-windup: integrate only when not saturated
            self._integral = candidate
        else:
            out = max(-self.out_limit, min(self.out_limit, out))
        return out
