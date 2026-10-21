#include <cstdlib>

#include "Enes100.h"
#include "PID_v1.h"
#include "Tank.h"

double x, y, r, theta;
double rTarget = 0, thetaTarget;
double rOutput, thetaOutput;
double xTolerance = 0.02, yTolerance = 0.02, thetaTolerance = 0.06;  // m, m, rad

const double KP = 1;
const double KI = 0;
const double KD = 0;

PID rPid(&r, &rOutput, &rTarget, KP, KI, KD, DIRECT);
PID thetaPid(&theta, &thetaOutput, &thetaTarget, KP, KI, KD, DIRECT);

void setup() {
  Tank.begin();
  Enes100.begin("FLO", FIRE, 17, 1201);
}

void makeTheta() {
  thetaPid.Compute();
  Tank.setLeftMotorPWM(-thetaOutput);
  Tank.setRightMotorPWM(thetaOutput);
}

void loop() {
  delay(20);  // 20ms event loop not bad

  x = Enes100.getX(), y = Enes100.getY(), theta = Enes100.getTheta();
  if (abs(theta - thetaTarget) < thetaTolerance) {
    makeTheta();
    return;
  }
}
