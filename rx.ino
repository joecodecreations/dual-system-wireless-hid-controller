#include <SPI.h>
#include <RF24.h>
#include <RF24Network.h>
#include <Mouse.h>
#include <Keyboard.h>

RF24 radio(7, 8);               // nRF24L01(+) radio attached using Getting Started board
RF24Network network(radio);     // Network uses that radio
const bool LogSerial = false;
const uint16_t this_node = 00;  // Address of our node in Octal format
const uint16_t other_node = 01; // Address of the other node in Octal format

// Structure of our payload
struct payload_t {
  uint8_t type;  // 0 for mouse movement, 1 for mouse click, 2 for keyboard input
  int8_t x;      // For mouse: x movement; For keyboard: key code; For click: button (1=left, 2=right)
  int8_t y;      // For mouse: y movement; For keyboard and click: not used
};

bool initialPayloadReceived = false;
int lastX = 0;
int lastY = 0;

void setup(void) {
  if (LogSerial) {
    Serial.begin(115200);
    while (!Serial) {
        // some boards need this because of native USB capability
    }

    Serial.println(F("Serial Started..."));
  }


  if (!radio.begin()) {
    if (LogSerial) {
        Serial.println(F("Radio hardware not responding!"));
    }

    while (1) {
      // hold in infinite loop
    }
  }
  radio.setPALevel(RF24_PA_MAX);  // Set power to maximum
  radio.setDataRate(RF24_2MBPS);  // Set data rate to 2Mbps
  radio.setChannel(90);
  network.begin(this_node);

  Mouse.begin();    // Initialize mouse control
  Keyboard.begin(); // Initialize keyboard control
}

void loop(void) {
  network.update();  // Check the network regularly

  while (network.available()) {  // Is there anything ready for us?
    RF24NetworkHeader header;    // If so, grab it
    payload_t payload;
    network.read(header, &payload, sizeof(payload));

    if (!initialPayloadReceived) {
      // Store the first received payload as the initial reference point
      lastX = payload.x;
      lastY = payload.y;
      initialPayloadReceived = true;

      if(LogSerial){
        Serial.println(F("Initial payload received. No mouse movement yet."));
      }
    } else {
      switch (payload.type) {
        case 0: {  // Mouse movement
          // Calculate the difference from the last payload
          int deltaX = payload.x - lastX;
          int deltaY = payload.y - lastY;

          // Move the mouse according to the difference
          Mouse.move(deltaX, deltaY);

          // Store the current payload as the last one for the next iteration
          lastX = payload.x;
          lastY = payload.y;

          // Debug output
          if(LogSerial){
            if (deltaX != 0 || deltaY != 0) {
                Serial.print(F("Mouse move X: "));
                Serial.print(deltaX);
                Serial.print(F(", Y: "));
                Serial.println(deltaY);
            }
          }
          break;
        }
        case 1: {  // Mouse click
          if (payload.x == 1) {
            Mouse.press(MOUSE_LEFT);
            if(LogSerial){
                Serial.println(F("Mouse Left Click"));
            }
          } else if (payload.x == 2) {
            Mouse.press(MOUSE_RIGHT);
            if(LogSerial){
                Serial.println(F("Mouse Right Click"));
            }
          } else if (payload.x == 3) {
            Mouse.release(MOUSE_LEFT);
            if(LogSerial){
                Serial.println(F("Mouse Left+Right Click"));
            }
          } else if (payload.x == 4) {
            Mouse.release(MOUSE_RIGHT);
          }
          break;
        }
        case 2: {  // Keyboard input
          Keyboard.press(payload.x);
          Keyboard.release(payload.x);
          if(LogSerial){
            Serial.print(F("Keyboard Press: "));
            Serial.println((char)payload.x);
          }
          break;
        }
      }
    }
  }
}
