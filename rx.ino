#include <SPI.h>
#include <RF24.h>
#include <RF24Network.h>
#include <Mouse.h>
#include <Keyboard.h>

RF24 radio(7, 8);               // nRF24L01(+) radio attached using Getting Started board
RF24Network network(radio);     // Network uses that radio
const bool LogSerial = true;
const uint16_t this_node = 00;  // Address of our node in Octal format
const uint16_t other_node = 01; // Address of the other node in Octal format

// Structure of our payload
struct payload_t {
  uint8_t type;  // 0 for mouse movement, 1 for mouse click, 2 for keyboard input
  int8_t x;      // For mouse: x movement; For keyboard: key code; For click: button (1=left, 2=right)
  int8_t y;      // For mouse: y movement; For keyboard and click: not used
  char message[128]; // message
  bool isPressed;
};

bool initialPayloadReceived = false;
int lastX = 0;
int lastY = 0;

struct KeyMap {
    const char* name;
    uint8_t keyCode;
};

KeyMap specialKeyMap[] = {
    {"KEY_LEFT_CTRL", KEY_LEFT_CTRL},
    {"KEY_LEFT_SHIFT", KEY_LEFT_SHIFT},
    {"KEY_LEFT_ALT", KEY_LEFT_ALT},
    {"KEY_LEFT_GUI", KEY_LEFT_GUI},  // Windows key on most keyboards
    {"KEY_RIGHT_CTRL", KEY_RIGHT_CTRL},
    {"KEY_RIGHT_SHIFT", KEY_RIGHT_SHIFT},
    {"KEY_RIGHT_ALT", KEY_RIGHT_ALT},
    {"KEY_RIGHT_GUI", KEY_RIGHT_GUI},  // Windows key on most keyboards
    
    {"KEY_UP_ARROW", KEY_UP_ARROW},
    {"KEY_DOWN_ARROW", KEY_DOWN_ARROW},
    {"KEY_LEFT_ARROW", KEY_LEFT_ARROW},
    {"KEY_RIGHT_ARROW", KEY_RIGHT_ARROW},
    
    {"KEY_BACKSPACE", KEY_BACKSPACE},
    {"KEY_TAB", KEY_TAB},
    {"KEY_RETURN", KEY_RETURN},      // Enter key
    {"KEY_ESC", KEY_ESC},
    {"KEY_INSERT", KEY_INSERT},
    {"KEY_DELETE", KEY_DELETE},
    {"KEY_PAGE_UP", KEY_PAGE_UP},
    {"KEY_PAGE_DOWN", KEY_PAGE_DOWN},
    {"KEY_HOME", KEY_HOME},
    {"KEY_END", KEY_END},
    
    {"KEY_CAPS_LOCK", KEY_CAPS_LOCK},
    {"KEY_F1", KEY_F1},
    {"KEY_F2", KEY_F2},
    {"KEY_F3", KEY_F3},
    {"KEY_F4", KEY_F4},
    {"KEY_F5", KEY_F5},
    {"KEY_F6", KEY_F6},
    {"KEY_F7", KEY_F7},
    {"KEY_F8", KEY_F8},
    {"KEY_F9", KEY_F9},
    {"KEY_F10", KEY_F10},
    {"KEY_F11", KEY_F11},
    {"KEY_F12", KEY_F12},

    {"KEY_PRINT_SCREEN", KEY_PRINT_SCREEN},
    {"KEY_SCROLL_LOCK", KEY_SCROLL_LOCK},
    {"KEY_PAUSE", KEY_PAUSE},

    {"KEY_NUM_LOCK", KEY_NUM_LOCK},

    {"KEYPAD_0", KEY_KP_0},   // Keypad 0
    {"KEYPAD_1", KEY_KP_1},   // Keypad 1
    {"KEYPAD_2", KEY_KP_2},   // Keypad 2
    {"KEYPAD_3", KEY_KP_3},   // Keypad 3
    {"KEYPAD_4", KEY_KP_4},   // Keypad 4
    {"KEYPAD_5", KEY_KP_5},   // Keypad 5
    {"KEYPAD_6", KEY_KP_6},   // Keypad 6
    {"KEYPAD_7", KEY_KP_7},   // Keypad 7
    {"KEYPAD_8", KEY_KP_8},   // Keypad 8
    {"KEYPAD_9", KEY_KP_9},   // Keypad 9

    {"KEYPAD_DIVIDE", KEY_KP_SLASH},      // Keypad /
    {"KEYPAD_MULTIPLY", KEY_KP_ASTERISK}, // Keypad *
    {"KEYPAD_SUBTRACT", KEY_KP_MINUS},    // Keypad -
    {"KEYPAD_ADD", KEY_KP_PLUS},          // Keypad +
    {"KEYPAD_ENTER", KEY_KP_ENTER},       // Keypad Enter
    {"KEYPAD_DOT", KEY_KP_DOT},           // Keypad .

    {"KEY_SPACE", ' '},  // Space can be represented by the space character


};

uint8_t findKeyCode(const char* keyName) {
    for (const auto& key : specialKeyMap) {
        if (strcmp(key.name, keyName) == 0) {
            return key.keyCode;
        }
    }
    return 0;  // Return 0 if not found, 0 usually means "no key"
}

void handleSpecialKey(const char* message, bool isPressed) {
    uint8_t keyCode = findKeyCode(message);
    if (keyCode != 0) {
        if (isPressed) {
            Keyboard.press(keyCode);
            Keyboard.release(keyCode);
        } else {
            Keyboard.release(keyCode);
        }
    }
}

void setup(void) {
  if (LogSerial) {
    Serial.begin(1000000);
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
            if(payload.isPressed){
                Mouse.press(MOUSE_LEFT);
            } else {
                Mouse.release(MOUSE_LEFT);
            }
            if(LogSerial){
                Serial.println(F("Mouse Left Click"));
            }
          } else if (payload.x == 2) {
            if(payload.isPressed){
                Mouse.press(MOUSE_RIGHT);
            } else {
                Mouse.release(MOUSE_RIGHT);
            }
            if(LogSerial){
                Serial.println(F("Mouse Right Click"));
            }
          }
          break;
        }
        case 2: {  // Keyboard input
          if(payload.isPressed){
            Keyboard.press(payload.x);
            Keyboard.release(payload.x);
          } else {
            Keyboard.release(payload.x);
          }
          if(LogSerial){
            Serial.print(F("Keyboard Press: "));
            Serial.println((char)payload.x);
          }
          break;
        }
        case 3: {  // Special key or string input
          handleSpecialKey(payload.message, payload.isPressed);
          if(LogSerial){
            Serial.print(F("Special Key Press: "));
            Serial.println(payload.message);
          }
          break;
        }
        case 4: {  // Key combinations
          if(LogSerial){
            Serial.print(F("Key Combinations: "));
            Serial.println(payload.message);
          }
          // get payload.message and split it by comma
          char* pch;
          pch = strtok(payload.message, ",");
          // do keyboard press for each key then release all 
          while (pch != NULL) {
            uint8_t keyCode = findKeyCode(pch);

            // if keyCode is not found then it is a character
            if (keyCode == 0) {
                Keyboard.press(pch[0]);
            } else if (keyCode != 0) {
                Keyboard.press(keyCode);
            }

            pch = strtok(NULL, ","); // this is to get the next token
          }
          Keyboard.releaseAll();
          break;
        }
        
      }
    }
  }
}
