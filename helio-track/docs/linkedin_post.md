# LinkedIn post drafts

## English (main)

I'm a mechatronics engineering prep-year student, and I wanted to learn control systems by building something real instead of waiting for the course. So I built **HelioTrack**, a dual-axis solar tracker.

What's inside:
- Solar geometry + clear-sky irradiance model in Python
- PID controller with anti-windup, deadband and slew-rate limiting
- Noisy light-sensor simulation to compare a fixed panel with a tracking panel
- Arduino/ESP32 firmware (4 LDR quadrant sensor, 2 servos, CSV telemetry)
- Unit tests, CI on GitHub Actions, wiring guide and bill of materials

The most useful lesson: my first PID gains were unstable. The controller output was a velocity command, so kp x sample-time was above 1, which makes a discrete loop oscillate. A unit test on pointing error caught it, and retuning cut the median error from about 9° to 0.35°.

In the idealised model (direct beam only, clear sky), tracking gives 27-76% more energy per day than a fixed south-facing panel at 41° latitude. Real-world gains are usually lower, so I'm treating this as a model to validate on hardware next.

Code, docs and plots: <GITHUB LINK>

I'd love feedback from anyone working in control, embedded systems or renewable energy.

#Mechatronics #ControlSystems #RenewableEnergy #Arduino #Python #Engineering #SolarEnergy

## Türkçe (kısa)

Mekatronik mühendisliği hazırlık öğrencisi olarak kontrol sistemlerini derse beklemeden gerçek bir projeyle öğrenmek istedim: **HelioTrack**, çift eksenli güneş takip sistemi. Python simülasyonu (güneş geometrisi, PID, sensör gürültüsü), Arduino/ESP32 yazılımı, testler, CI ve donanım rehberi GitHub'da: <GITHUB LINK>

Not: İlk PID kazançlarım kararsız çıktı; birim testi yakaladı, ayarlayınca medyan yönelme hatası ~9°'den 0,35°'ye düştü. Geri bildirime açığım!
