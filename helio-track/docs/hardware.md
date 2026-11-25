# Hardware guide

## Bill of materials (approx. 20-30 USD)

| Qty | Part | Notes |
|----:|------|-------|
| 1 | Arduino Nano / Uno or ESP32 dev board | ESP32 needs the ESP32Servo library |
| 4 | LDR (photoresistor), GL5528 or similar | one per quadrant |
| 4 | 10 kΩ resistor | voltage divider for each LDR |
| 2 | SG90 / MG90S micro servo (MG996R for a heavier panel) | azimuth + elevation |
| 1 | Small solar panel (5-6 V, ~1 W) | optional, for a demo load |
| 1 | External 5 V supply, 2 A | **do not power servos from the board's 5 V pin** |
| - | 3D-printed or cardboard pan/tilt bracket, cross-shaped light divider | STL files can be added to `cad/` |

## Wiring

```
        5V ──┬──────┬──────┬──────┐
            LDR TL  LDR TR LDR BL LDR BR
             ├─A0   ├─A1   ├─A2   ├─A3     (analog inputs)
            10k     10k    10k    10k
             │       │      │      │
GND ─────────┴───────┴──────┴──────┘

Servo AZ signal → D9      Servo EL signal → D10
Servo power: external 5 V supply, GND shared with the board
```

## Sensor layout

```
   ┌─────┬─────┐   The cross-shaped divider casts a shadow on the LDRs
   │ TL  │ TR  │   that are NOT facing the sun. Equal readings on all
   ├─────┼─────┤   four mean the panel is perpendicular to the sun.
   │ BL  │ BR  │
   └─────┴─────┘
```

## Bring-up checklist

1. Upload the sketch with servos disconnected; open Serial Monitor at 115200 baud and check that all four readings move when you cover each LDR.
2. Connect servos and shine a torch from the left: the azimuth servo must turn toward it. If it turns away, flip the sign of `errAz` (same for elevation).
3. Tune `KP` upward until the panel tracks quickly, then back off 30% if it oscillates. Log the CSV and plot it.
4. Mount the panel and test outdoors.
