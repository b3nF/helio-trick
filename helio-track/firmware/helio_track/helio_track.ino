/*
 * HelioTrack firmware: dual-axis solar tracker (Arduino Nano/Uno or ESP32)
 *
 * Four LDRs in a quadrant layout separated by a cross-shaped shade divider.
 * When the panel points at the sun all four read the same; any imbalance is
 * the pointing error. A PID loop per axis drives two hobby servos.
 *
 *   A0 = top-left   A1 = top-right   A2 = bottom-left   A3 = bottom-right
 *   D9 = azimuth servo               D10 = elevation servo
 *
 * Each LDR forms a divider with a 10k resistor to GND (LDR to 5V/3.3V).
 * On ESP32 use the ESP32Servo library and pins that support ADC1.
 * Serial output is CSV at 115200 baud: ms,errAz,errEl,posAz,posEl
 */
#include <Servo.h>

// ---------- Pins ----------
const uint8_t PIN_TL = A0, PIN_TR = A1, PIN_BL = A2, PIN_BR = A3;
const uint8_t PIN_SERVO_AZ = 9, PIN_SERVO_EL = 10;

// ---------- Tuning ----------
const unsigned long LOOP_MS = 50;      // control period
const float KP = 2.0f;                 // degrees per loop per unit of normalised error (-1..1)
const float KI = 0.2f;
const float KD = 0.0f;
const float MAX_STEP_DEG = 0.6f;       // slew limit per loop (protects gears)
const float DEADBAND = 0.04f;          // normalised error below which we do nothing
const int   LIGHT_MIN = 150;           // average ADC reading below this = night/overcast
const float AZ_MIN = 10, AZ_MAX = 170; // servo travel limits (degrees)
const float EL_MIN = 10, EL_MAX = 90;
const float AZ_PARK = 10, EL_PARK = 20; // park facing sunrise
const float ALPHA = 0.25f;             // low-pass filter (0..1), higher = faster

struct Pid {
  float kp, ki, kd, integral, prev;
  float update(float err, float dt) {
    if (fabs(err) < DEADBAND) { integral *= 0.9f; prev = err; return 0.0f; }
    float d = (err - prev) / dt;
    prev = err;
    float cand = integral + err * dt;
    float out = kp * err + ki * cand + kd * d;
    if (fabs(out) < MAX_STEP_DEG) integral = cand;      // anti-windup
    else out = constrain(out, -MAX_STEP_DEG, MAX_STEP_DEG);
    return out;
  }
};

Servo servoAz, servoEl;
Pid pidAz = {KP, KI, KD, 0, 0};
Pid pidEl = {KP, KI, KD, 0, 0};
float posAz = AZ_PARK, posEl = EL_PARK;
float fTL = 0, fTR = 0, fBL = 0, fBR = 0;
unsigned long lastRun = 0;

void setup() {
  Serial.begin(115200);
  servoAz.attach(PIN_SERVO_AZ);
  servoEl.attach(PIN_SERVO_EL);
  servoAz.write((int)posAz);
  servoEl.write((int)posEl);
  fTL = analogRead(PIN_TL); fTR = analogRead(PIN_TR);
  fBL = analogRead(PIN_BL); fBR = analogRead(PIN_BR);
  Serial.println(F("ms,errAz,errEl,posAz,posEl"));
}

void loop() {
  unsigned long now = millis();
  if (now - lastRun < LOOP_MS) return;
  float dt = (now - lastRun) / 1000.0f;
  lastRun = now;

  // Low-pass filter each sensor to suppress noise and passing shadows
  fTL += ALPHA * (analogRead(PIN_TL) - fTL);
  fTR += ALPHA * (analogRead(PIN_TR) - fTR);
  fBL += ALPHA * (analogRead(PIN_BL) - fBL);
  fBR += ALPHA * (analogRead(PIN_BR) - fBR);

  float total = fTL + fTR + fBL + fBR;
  float errAz = 0, errEl = 0;

  if (total / 4.0f > LIGHT_MIN) {
    // Normalised imbalance (-1..1): independent of overall brightness
    float left  = fTL + fBL, right  = fTR + fBR;
    float top   = fTL + fTR, bottom = fBL + fBR;
    errAz = (right - left)  / total;
    errEl = (top   - bottom) / total;
    // Sign convention: flip these if your mechanics move the wrong way.
    posAz += pidAz.update(errAz, dt);   // output is degrees to move this loop (<= MAX_STEP_DEG)
    posEl += pidEl.update(errEl, dt);
  } else {
    // Night: slowly return to park position
    posAz += constrain(AZ_PARK - posAz, -0.1f, 0.1f);
    posEl += constrain(EL_PARK - posEl, -0.1f, 0.1f);
    pidAz.integral = pidEl.integral = 0;
  }

  posAz = constrain(posAz, AZ_MIN, AZ_MAX);
  posEl = constrain(posEl, EL_MIN, EL_MAX);
  servoAz.write((int)posAz);
  servoEl.write((int)posEl);

  Serial.print(now);   Serial.print(',');
  Serial.print(errAz, 3); Serial.print(',');
  Serial.print(errEl, 3); Serial.print(',');
  Serial.print(posAz, 1); Serial.print(',');
  Serial.println(posEl, 1);
}
