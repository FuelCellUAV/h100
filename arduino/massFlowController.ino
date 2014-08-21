#include <Wire.h>
const int sensorPin = A0; const int ledPin = 13; float flowRate = 0.0; void setup() {
  pinMode(ledPin, OUTPUT);
  Wire.begin(0x2C); // join i2c bus with address #4
  Wire.onRequest(requestEvent); // register event
  Serial.begin(57600); // start serial for output
}
void loop() {
  float rate = float(analogRead(sensorPin)); // From ml/min to litres/min
  flowRate = rate * 0.00244140625;
  Serial.println(flowRate, 4); // Print to UART
  blinky(); // Flash the LED
  delay(500);
}
void requestEvent() {
  byte data[2];
  data[0] = int(flowRate*1000.0) >> 8;
  data[1] = int(flowRate*1000.0) & 0xff;
  Wire.write(data, 2);
  blinky(); // Flash the LED
}
void blinky() {
  digitalWrite(ledPin, !digitalRead(ledPin));
}

