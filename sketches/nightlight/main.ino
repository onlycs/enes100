#define LED_PIN 9
#define CUTOFF 880
#define PHOTORESISTOR_PIN A0

void setup() {
  pinMode(LED_PIN, OUTPUT);
  Serial.begin(115200);
}

void loop() {
  Serial.println(analogRead(PHOTORESISTOR_PIN));

  if (analogRead(PHOTORESISTOR_PIN) > CUTOFF) {
    digitalWrite(LED_PIN, HIGH);
  } else {
    digitalWrite(LED_PIN, LOW);
  }

  delay(150);
}
