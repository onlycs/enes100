const uint8_t LEDS[] = {13, 12, 11};
const int LEDS_SIZE = sizeof(LEDS) / sizeof(LEDS[0]);
const unsigned long INTERVAL = 250;

uint8_t current = 0;

void setup() {
  for (int i = 0; i < LEDS_SIZE; i++) pinMode(LEDS[i], OUTPUT);
  Serial.begin(115200);
}

void loop() {
  for (int i = 0; i < LEDS_SIZE; i++) {
    if (current == i)
      digitalWrite(LEDS[i], HIGH);
    else
      digitalWrite(LEDS[i], LOW);
  }

  current += 1;
  current %= LEDS_SIZE;

  delay(INTERVAL);
}
