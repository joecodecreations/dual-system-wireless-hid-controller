#include <SPI.h>
#include <RF24.h>
#include <RF24Network.h>

RF24 radio(7, 8);               // nRF24L01(+) radio attached using Getting Started board
RF24Network network(radio);     // Network uses that radio

const uint16_t this_node = 01;  // Address of our node in Octal format
const uint16_t other_node = 00; // Address of the other node in Octal format
// add string for message
String eventMessage = "";
// Structure of our payload
struct payload_t {
  uint8_t type;  // 0 for mouse movement, 1 for mouse click, 2 for keyboard input
  int8_t x;      // x movement or key/button code
  int8_t y;      // y movement, not used for clicks/keyboard
};

bool receiving = false;
payload_t payload;

void setup() {
  Serial.begin(9600);
  while (!Serial) {
    // Wait for serial port to connect (only needed on native USB boards)
  }
  Serial.println(F("Serial Started..."));

  if (!radio.begin()) {
    Serial.println(F("Radio hardware not responding!"));
    while (1);  // Infinite loop if radio fails to start
  }

  // Increase power and speed
  radio.setPALevel(RF24_PA_MAX);     // Set power to maximum
  radio.setDataRate(RF24_2MBPS);     // Set data rate to 2Mbps

  radio.setChannel(90);              // Set the channel to 90 (or your preferred channel)
  network.begin(this_node);          // Start the network
  Serial.println(F("RF24 Network Started..."));
}

void loop() {
  // Check for incoming serial data
  if (Serial.available()) {
    String inputString = Serial.readStringUntil('\n');  // Read until newline
    inputString.trim();  // Remove any extraneous whitespace

    if (inputString.startsWith("M")) {
      eventMessage = "Sending Mouse Movement";
      receiving = true;  // Start receiving mouse data
      int commaIndex = inputString.indexOf(',');
      
      // Split the string into x and y parts
      String xStr = inputString.substring(2, commaIndex);
      String yStr = inputString.substring(commaIndex + 1);

      // Convert the strings to int8_t values
      int8_t xValue = (int8_t)xStr.toInt();
      int8_t yValue = (int8_t)yStr.toInt();

      // Scale the x and y values (adjust for sensitivity)
      xValue *= 1;
      yValue *= 1;

      // Limit xValue and yValue to the int8_t range (-128 to 127) to prevent overflow
      xValue = constrain(xValue, -128, 127);
      yValue = constrain(yValue, -128, 127);

      payload.type = 0;  // Mouse movement
      payload.x = xValue;
      payload.y = yValue;
      
    } else if (inputString.startsWith("S")) {
      eventMessage = "Sending Mouse Scroll";
      receiving = false;  // Stop receiving mouse data

    } else if (inputString.startsWith("C,")) {  // Mouse click: C,button
      eventMessage = "Sending Mouse Click";
      int button = inputString.substring(2).toInt();
      payload.type = 1;  // Mouse click
      payload.x = button;  // 1 for left, 2 for right
      payload.y = 0;       // Not used

    } else if (inputString.startsWith("K,")) {  // Keyboard input: K,keycode
      eventMessage = "Sending keyboard type";
      char keyCode = inputString.charAt(2);
      payload.type = 2;  // Keyboard input
      payload.x = keyCode;  // ASCII code of the key
      payload.y = 0;        // Not used
    }

    // Send the payload over the RF24 network
    RF24NetworkHeader header(other_node);
    bool ok = network.write(header, &payload, sizeof(payload));
    Serial.println(ok ? eventMessage : eventMessage + " -- Failed");
  }

  // Update the RF24 network regularly
  network.update();
}