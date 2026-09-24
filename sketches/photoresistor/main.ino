#include <cstdint>

#include "api/Common.h"
const uint8_t PIN = A0;
const uint32_t BAUD = 115200;

void setup() {
  Serial.begin(BAUD);
}

void loop() {
  uint32_t light = analogRead(PIN);
  Serial.println(light);
  delay(250);
}
