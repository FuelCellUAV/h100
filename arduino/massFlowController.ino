// Mass Flow Controller Datalogger and ESC Driver

// Copyright (C) 2014  Simon Howroyd
// 
//     This program is free software: you can redistribute it and/or modify
//     it under the terms of the GNU General Public License as published by
//     the Free Software Foundation, either version 3 of the License, or
//     (at your option) any later version.
// 
//     This program is distributed in the hope that it will be useful,
//     but WITHOUT ANY WARRANTY; without even the implied warranty of
//     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
//     GNU General Public License for more details.
// 
//     You should have received a copy of the GNU General Public License
//     along with this program.  If not, see <http://www.gnu.org/licenses/>.

/////////////////////////////////////////////////////////////////////////////

// Include Libraries
#include <Servo.h>
#include <Wire.h>

// Define constants & variables
const int sensorPin = A1;
const int escPin = A0;
const int escPin2 = 53; // Mirror
const float calibration = 0.00244140625;
Servo speed_controller;
Servo speed_controller2; // Mirror
float flowRate = 0.0;
int throttle = 0;

// Setup method, runs once on startup
void setup()
{
  // Define the onbard LED as an output
  pinMode(LED_BUILTIN, OUTPUT);
  
  // Define the speed controller and it's mirror
  speed_controller.attach(escPin);
  speed_controller.attach(escPin2);
  
  // Start the I2C databus
  Wire.begin(0x2C);             // join i2c bus with address #4
  Wire.onRequest(requestEvent); // register event
  Wire.onReceive(receiveEvent); // register event

  // Start the serial connection for USB logging
  Serial.begin(115200);         // start serial for output
}


// Main method, loops for infinity
void loop()
{
  // Write the throttle value in memory to the ESC
  speed_controller.writeMicroseconds(map(throttle, 0, 100, 900, 2100));
  speed_controller2.writeMicroseconds(map(throttle, 0, 100, 900, 2100));

  // Read the mass flow rate
  float rate = float(analogRead(sensorPin)); // From ml/min to litres/min
  flowRate = rate * calibration; // Calibrate
  
  // Print the data to USB
  Serial.print(throttle);                // Print to UART
  Serial.print('\t');
  Serial.println(flowRate, 4);

  //Flash the onboard LED
  blinky();
  
  // Sleep to allow serial buffers to catch up
  delay(50);
}

// When asked for data over the I2C databus...
void requestEvent()
{
  // Define a variable to temporarily hold the data
  byte data[2];
  
  // Split the 16bit flowrate into two 8bit numbers for sending
  data[0] = int(flowRate*1000.0) >> 8;
  data[1] = int(flowRate*1000.0) & 0xff;
  
  // Send the data
  Wire.write(data, 2);
}

// When sent data over the I2C databus...
void receiveEvent(int num_bytes)
{
  // Read all data but the last received (clears the buffer of old data)
  while(1 < Wire.available())
  {
    Wire.read();
  }
  
  // Receive the most recent bit of data from the I2C databus
  int x = Wire.read();
  
  // Perform a sanity check on the data before saving it
  if (x <= 100 && x >= 0) {
    throttle = x;
  }
}

// FlipFlop method to flash the onboard LED
void blinky()
{
  digitalWrite(LED_BUILTIN, !digitalRead(LED_BUILTIN));
}
