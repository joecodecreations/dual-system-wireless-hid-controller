# Author : Joey Sanchez 2024
# Decription: Wireless HID Controller for controlling two computers with one keyboard and mouse
# Repository: https://github.com/joecodecreations/dual-system-wireless-hid-controller 
# Systems Supported: Windows, Mac, Linux


import serial
import serial.tools.list_ports
import pyautogui
import mouse
import time
import keyboard
from screeninfo import get_monitors
import tkinter as tk
import threading
from flask import Flask, request, jsonify
# Configuration
host_system = "windows"  # Options: "windows", "linux", "mac"
target_system = "windows"  # Options: "windows", "linux", "mac"
microprocessor_port = None  # Set to None to auto-detect the port
SERVER_PORT = 5000
ser = None # Serial port object for the microcontroller
# Global variables
mouse_left_click = False
mouse_right_click = False
mouse_left_released = False
mouse_right_released = False
allow_target_mouse_switching = True
log_microcontroller_messages = True
log_operational_messages = True
log_mouse_movement = False
log_key_presses = False
web_request = False
# Track sent mouse actions
mlc_sent = False  # Left click sent
mrc_sent = False  # Right click sent
mlcr_sent = False  # Left click released sent
mrcr_sent = False  # Right click released sent
special_keys_pressed = set()  # Initialize the set
isSpecialKeyPressed = False
keyboard_wait = False

off_system = False


monitors = get_monitors()
right_monitor = max(monitors, key=lambda m: m.x)

# Host computer's screen dimensions
host_width = right_monitor.width
host_height = right_monitor.height

# Target computer's screen dimensions (e.g., MacBook Air M2 Retina)
target_width = 2560  # Width of the target computer's screen
target_height = 1600  # Height of the target computer's screen

edge_threshold = 40
off_system = False
last_keys_pressed = set()  # Initialize the set


key_mapping = {
    "windows": {
        "ctrl": "ctrl",
        "alt": "alt",
        "win": "cmd",  # Treat Win on Windows as Cmd on Mac
        "shift": "shift",
        "delete": "delete",
        "backspace": "backspace",
        "enter": "enter",
        "home": "home",
        "end": "end",
        "pageup": "page up",
        "pagedown": "page down",
        "esc": "esc",
        "tab": "tab",
        "space": "space",
        "cmd": "win",  # Treat CMD on Mac as Win on Windows
        "left windows": "cmd",
    },
    "mac": {
        "ctrl": "ctrl",
        "option": "alt",  # Treat Option on Mac as Alt on Windows/Linux
        "cmd": "cmd",
        "shift": "shift",
        "delete": "backspace",  # Mac delete is equivalent to backspace
        "fn+delete": "delete",
        "return": "enter",
        "home": "home",
        "end": "end",
        "pageup": "page up",
        "pagedown": "page down",
        "esc": "esc",
        "tab": "tab",
        "space": "space",
        "super": "cmd",  # Treat Super on Linux as CMD on Mac
    },
    "linux": {
        "ctrl": "ctrl",
        "alt": "alt",
        "super": "super",
        "shift": "shift",
        "delete": "delete",
        "backspace": "backspace",
        "enter": "enter",
        "home": "home",
        "end": "end",
        "pageup": "page up",
        "pagedown": "page down",
        "esc": "esc",
        "tab": "tab",
        "space": "space",
        "cmd": "super"  # Treat CMD on Mac as Super on Linux
    }
}

special_key_map = {
    "shift": "KEY_LEFT_SHIFT",
    "ctrl": "KEY_LEFT_CTRL",
    "alt": "KEY_LEFT_ALT",
    "space": "KEY_SPACE",
    "enter": "KEY_RETURN",
    "backspace": "KEY_BACKSPACE",
    "tab": "KEY_TAB",
    "esc": "KEY_ESC",
    "up": "KEY_UP_ARROW",
    "down": "KEY_DOWN_ARROW",
    "left": "KEY_LEFT_ARROW",
    "right": "KEY_RIGHT_ARROW",
    "capslock": "KEY_CAPS_LOCK",
    "delete": "KEY_DELETE",
    "home": "KEY_HOME",
    "end": "KEY_END",
    "page up": "KEY_PAGE_UP",
    "page down": "KEY_PAGE_DOWN",
    "insert": "KEY_INSERT",
    "print screen": "KEY_PRINT_SCREEN",
    "pause": "KEY_PAUSE",
    "cmd": "KEY_LEFT_GUI",
    "win": "KEY_LEFT_GUI",
    "super": "KEY_LEFT_GUI",
    "option": "KEY_LEFT_ALT",
    "right gui": "KEY_RIGHT_GUI",
    "right shift": "KEY_RIGHT_SHIFT",
    "right alt": "KEY_RIGHT_ALT",
    "right control": "KEY_RIGHT_CTRL",
    "left gui": "KEY_LEFT_GUI",
}

# Arduino-specific mapping using Keyboard.h
special_key_map = {
    "shift": "KEY_LEFT_SHIFT",
    "ctrl": "KEY_LEFT_CTRL",
    "alt": "KEY_LEFT_ALT",
    "space": "KEY_SPACE",
    "enter": "KEY_RETURN",
    "backspace": "KEY_BACKSPACE",
    "tab": "KEY_TAB",
    "esc": "KEY_ESC",
    "up": "KEY_UP_ARROW",
    "down": "KEY_DOWN_ARROW",
    "left": "KEY_LEFT_ARROW",
    "right": "KEY_RIGHT_ARROW",
    "capslock": "KEY_CAPS_LOCK",
    "delete": "KEY_DELETE",
    "home": "KEY_HOME",
    "end": "KEY_END",
    "page up": "KEY_PAGE_UP",
    "page down": "KEY_PAGE_DOWN",
    "insert": "KEY_INSERT",
    "print screen": "KEY_PRINT_SCREEN",
    "pause": "KEY_PAUSE",
    "cmd": "KEY_LEFT_GUI",
    "win": "KEY_LEFT_GUI",
    "super": "KEY_LEFT_GUI",
    "option": "KEY_LEFT_ALT",
    "right gui": "KEY_RIGHT_GUI",
    "right shift": "KEY_RIGHT_SHIFT",
    "right alt": "KEY_RIGHT_ALT",
    "right control": "KEY_RIGHT_CTRL",
    "left gui": "KEY_LEFT_GUI",
}

# Create a Tkinter root window
root = tk.Tk()
root.overrideredirect(True)  # Remove window decorations (title bar, etc.)
root.attributes("-topmost", True)  # Keep the window on top
root.geometry(f"10x10+{right_monitor.x + right_monitor.width - 20}+{right_monitor.y + right_monitor.height - 20}")  # Position the window


# Create a label to display the icon (a simple colored square in this example)
icon_label = tk.Label(root, bg="red")
icon_label.pack(fill=tk.BOTH, expand=True)


app = Flask(__name__)

def start_flask():
    app.run(host="0.0.0.0", port=SERVER_PORT)


@app.route('/keypress', methods=['POST'])
def keypress():
    global off_system, web_request
    old_off_system = off_system
    try:
        key = request.json.get('key')
        if key:
            # Create a KeyboardEvent with a dummy scan_code
            key_event = keyboard.KeyboardEvent(event_type='down', name=key, scan_code=0, time=time.time(), device=None, is_keypad=False)
            web_request = True
            off_system = True
            handleKeys(key_event)
            off_system = old_off_system
            # web_request = False
            time.sleep(0.1)
            return jsonify({"status": "success", "key": key}), 200
        return jsonify({"status": "error", "message": "No key provided"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@app.route('/multikeypress', methods=['POST'])
def multikeypress():
    global off_system, web_request
    old_off_system = off_system
    try:
        string = request.json.get('content')
        # for each character in the string
        for key in string:
            # Create a KeyboardEvent with a dummy scan_code
            key_event = keyboard.KeyboardEvent(event_type='down', name=key, scan_code=0, time=time.time(), device=None, is_keypad=False)
            web_request = True
            off_system = True
            handleKeys(key_event)
            off_system = old_off_system
            # web_request = False
        return jsonify({"status": "success", "string": string}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@app.route('/turnoff-keyboard-mouse', methods=['POST'])
def turnoff_keyboard_mouse():
    global allow_target_mouse_switching
    try:
        allow_target_mouse_switching = False
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@app.route('/turnon-keyboard-mouse', methods=['POST'])
def turnon_keyboard_mouse():
    global allow_target_mouse_switching
    try:
        allow_target_mouse_switching = True
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/mouse_click', methods=['POST'])
def mouse_click():
    try:
        button = request.json.get('button')
        action = request.json.get('action')
        if button and action:
            if button == 'left':
                if action == 'down':
                    on_left_click()
                elif action == 'up':
                    on_left_release()
            elif button == 'right':
                if action == 'down':
                    on_right_click()
                elif action == 'up':
                    on_right_release()
            else:
                return jsonify({"status": "error", "message": "Invalid button"}), 400
            return jsonify({"status": "success", "button": button, "action": action}), 200
        return jsonify({"status": "error", "message": "No button or action provided"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Define an array of keys that don't require the Shift key
keys_without_shift = [
    "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p",
    "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "1", "2", "3", "4", "5", "6",
    "7", "8", "9", "0", "`", "-", "=", "[", "]", ";", "'", ",", ".", "/", "\\",
    "A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P",
    "Q", "R", "S", "T", "U", "V", "W", "X", "Y", "Z", "!", "@", "#", "$", "%", "^",
    "&", "*", "(", ")", "_", "+", "{", "}", "|", ":", '"', "<", ">", "?"
    
]
keys_with_shift = ["~", "!", "@", "#", "$", "%", "^", "&", "*", "(", ")", "_", "+", "{", "}", "|", ":", '"', "<", ">", "?"]
special_keys = [
    "shift",
    "ctrl",
    "alt",
    "space",
    "enter",
    "backspace",
    "tab",
    "esc",
    "up",
    "down",
    "left",
    "right",
    "capslock",
    "delete",
    "home",
    "end",
    "page up",
    "page down",
    "insert",
    "print screen",
    "pause",
    "cmd",
    "win",
    "super",
    "option",
    "right gui",
    "right shift",
    "right alt",
    "right control",
    "left gui",
    "left shift",
    "left alt",
    "left control",
    "left windows",
    "right windows",
]


def check_position():
    global off_system, log_mouse_movement, log_operational_messages
    try:
        x, y = mouse.get_position()

        if log_mouse_movement:
            print(f"Mouse position: x={x}, y={y} | Off-system: {off_system}")

        if right_monitor.y <= y <= right_monitor.y + right_monitor.height:
            if (
                x >= right_monitor.x + right_monitor.width - edge_threshold
                and not off_system
            ):
                if allow_target_mouse_switching:
                    off_system = True
                    connect_keyboard_listeners(True)
                    show_icon()  # Show the icon when switching to the target system
                    if log_operational_messages:
                        print("Switching to target system...")

                    mouse.move(right_monitor.x - 10000, y)  # Move cursor off-screen
                    time.sleep(0.1)

            elif x <= right_monitor.x + edge_threshold and off_system:
                off_system = False
                remove_keyboard_listeners()
                hide_icon()  # Hide the icon when switching back to the host system
                if log_operational_messages:
                    print("Switching back to host system...")

                move_to_relative(right_monitor.width - 2, y - right_monitor.y)
                time.sleep(0.2)

        if off_system and allow_target_mouse_switching:
            if log_mouse_movement:
                print(f"Sending x={x}, y={y}")
            ser.write(f"M{x},{y}\n".encode())

    except Exception as e:
        print(f"Error occurred in loop: {e}")
    
    root.update_idletasks()  # Update Tkinter window
    root.update()  # Process Tkinter events

def find_microprocessor_port():
    ports = list(serial.tools.list_ports.comports())
    for port in ports:
        # print(port.description)
        if (
            any(
                keyword in port.description
                for keyword in [
                    "Leonardo",
                    "Pro Micro",
                    "Uno",
                    "Mega",
                    "Arduino",
                    "USB Serial Device",  # Add comma here
                    "Microsoft Natural Ergonomic Keyboard 4000",
                ]
            )
            # or port.device == "COM24"
        ):
            print("Starting COMs with" + port.device)
            return port.device
    return None

def scale_movement(value, host_max, target_max):
    """Scale movement from host screen size to target screen size."""
    return int((value / host_max) * target_max)

def move_to_relative(x, y):
    absolute_x = right_monitor.x + x
    absolute_y = right_monitor.y + y
    mouse.move(absolute_x, absolute_y)

    if log_mouse_movement:
        print(f"Moved cursor to relative x={x}, y={y} on rightmost monitor")

def on_left_click():
    global mlc_sent, mlcr_sent, mouse_left_click, mouse_left_released  # Global declaration

    mouse_left_click = True
    mlcr_sent = False
    mlc_sent = True
    mouse_left_released = False
    ser.write(f"C,1\n".encode())
    if log_key_presses:
        print("Left mouse button pressed")

def on_right_click():
    global mrc_sent, mrcr_sent, mouse_right_click, mouse_right_released  # Global declaration
    
    mouse_right_click = True
    mrcr_sent = False
    mouse_right_released = False
    mrc_sent = True
    ser.write(f"C,3\n".encode())
    if log_key_presses:
        print("Right mouse button clicked")

def on_left_release():
    global mlc_sent, mlcr_sent, mouse_left_click, mouse_left_released  # Global declaration
    # if not mlcr_sent:
    mouse_left_released = True
    mlc_sent = False
    mouse_left_click = False
    mlcr_sent = True
    ser.write(f"C,2\n".encode())
    if log_key_presses:
        print("Left mouse button released")

def on_right_release():
    global mrc_sent, mrcr_sent, mouse_right_click, mouse_right_released  # Global declaration
    # if not mrcr_sent:
    mouse_right_released = True
    mrc_sent = False
    mouse_right_click = False
    mrcr_sent = True
    ser.write(f"C,4\n".encode())
    if log_key_presses:
        print("Right mouse button released")

def show_icon():
    root.deiconify()  # Show the window

def hide_icon():
    root.withdraw()  # Hide the window

def connect_keyboard_listeners(prevent_system_output=False):
    global off_system
    if off_system:
        prevent_system_output = True
    keyboard.unhook(keyboard.on_press(handleKeys))
    keyboard.on_press(handleKeys, suppress=prevent_system_output)

def map_key_to_arduino(input_os, target_os, key_pressed):
    # Normalize the key name to lowercase
    key_pressed_lowered = key_pressed.lower()

    # Step 1: Convert the key from the input OS to a general target key
    if input_os not in key_mapping:
        return key_pressed  # Unsupported OS

    target_key_intermediate = key_mapping[input_os].get(key_pressed_lowered, key_pressed_lowered)

    # Step 2: Convert the intermediate key to the target OS key
    if target_os not in key_mapping:
        return key_pressed  # Unsupported OS

    target_key_final = key_mapping[target_os].get(target_key_intermediate, target_key_intermediate)

    # Step 3: Map the final target key to an Arduino key code
    arduino_key_code = special_key_map.get(target_key_final.lower())

    if arduino_key_code:
        return arduino_key_code
    else:
        return target_key_final  # No mapping found, return the intermediate key as a fallback
  
def send_Keys(handleSpecialKeys):
    global special_keys_pressed, isSpecialKeyPressed, target_system, keyboard_wait
    try:
        if not special_keys_pressed:
            print("No key pressed")
            return
        isSpecialKeyPressed = False
        keyboard_wait = False
        keys_to_send = set()

        # map special_key = special_key_map[key.name] for each key in special_keys_pressed or return character
        for key in special_keys_pressed:
            if key in special_keys:
                special_key_mapped = map_key_to_arduino(host_system, target_system, key)
                if special_key_mapped is None:
                    special_key_mapped = key
                keys_to_send.add(special_key_mapped)
                break
            else:
                keys_to_send.add(key)


        # add back in any missing single characters to the list of keys to send
        for key in special_keys_pressed:
            if key not in keys_to_send and len(key) == 1:
                keys_to_send.add(key)
        # always make sure the keys to send are in the order of longest keys first
        keys_to_send = sorted(keys_to_send, key=len, reverse=True)

        if len(keys_to_send) == 1:
            key = next(iter(special_keys_pressed))
            if key in special_keys:
                key = map_key_to_arduino(host_system, target_system, key)
                ser.write(f"S,{key}\n".encode())
            else:
                ser.write(f"K,{key}\n".encode())
            if log_key_presses:
                print(f"Special Key pressed: {key}")
        else:
            ser.write(f"X,{','.join(keys_to_send)}\n".encode())
            if log_key_presses:
                print(f"Multiple keys pressed: {','.join(keys_to_send)}")

        special_keys_pressed.clear()

    except Exception as e:
        print(f"Error while sending keys: {e}")
        
def handleSpecialKeys(key):
    # print('special keys')
    global keyboard_wait, special_keys, off_system, isSpecialKeyPressed, special_keys_pressed
    if off_system or web_request:
        if key.name in special_keys:
                if key.event_type == keyboard.KEY_DOWN:
                    # if we didnt already press the special key
                    if key.name not in special_keys_pressed:
                        # add it to our array of key combinations
                        if log_key_presses:
                            print(f"Special Key Added To Combo: {key.name}")
                
                        special_keys_pressed.add(key.name)
                        # track that we have pressed a special key so that all regular keys get added to combo
                        isSpecialKeyPressed = True
                        if log_key_presses:
                            print(f"Special Key pressed DOWN: {key.name}")
                        if web_request:
                            send_Keys(handleSpecialKeys)
                        else:
                            keyboard.hook_key(key.name, handleSpecialKeys)
                if key.event_type == keyboard.KEY_UP and key.name in special_keys_pressed:
                    if log_key_presses:
                        print(f"Special Key released: {key.name}")
                    send_Keys(handleSpecialKeys)
                    connect_keyboard_listeners(True)

def handleKeys(key):
    global target_system, keyboard_wait, off_system, isSpecialKeyPressed, special_keys_pressed,keys_without_shift, keys_with_shift
    # print('handle keys called')
    print(key.name)
    if key.name in special_keys:
        handleSpecialKeys(key)
    if off_system or web_request:
        character = key.name
        # handle key combinations
        if isSpecialKeyPressed:
            print(f"Regular Key Added To Combo: {key.name}")
            if key.event_type == keyboard.KEY_DOWN:
                if web_request:
                    ser.write(f"S,{key.name}\n".encode())
                    if log_key_presses:
                        print(f"Key pressed DOWN: {key.name}")
                else:
                    special_keys_pressed.add(key.name)
                    if log_operational_messages:
                        print(f"Key Combo gathering....adding: {key.name}")

        else:
            # handle regular typing 
            character = key.name
            if character in keys_without_shift or character in keys_with_shift:
                if not keyboard_wait or web_request:
                    keyboard_wait = True
                    if key.event_type == keyboard.KEY_DOWN:
                        ser.write(f"K,{key.name}\n".encode())
                        if log_key_presses:
                            print(f"Key pressed DOWN: {key.name}")
                        keyboard_wait = False
                else:
                    print('keyboard waiting')

def handleMouseClick(event):
    global off_system

    # Ensure the event is a ButtonEvent (ignoring MoveEvent, WheelEvent, etc.)
    if off_system and isinstance(event, mouse.ButtonEvent):
        event_type = event.event_type
        button = event.button
        pressed = event_type == "down"

        if button == mouse.LEFT:
            if pressed:
                on_left_click()
            else:
                on_left_release()
        elif button == mouse.RIGHT:
            if pressed:
                on_right_click()
            else:
                on_right_release()

def remove_keyboard_listeners():
    if log_operational_messages:
        print("Removing keyboard listeners")
    keyboard.unhook_all()

def on_left_click():
    global mlc_sent, mlcr_sent, mouse_left_click, mouse_left_released
    mouse_left_click = True
    mlcr_sent = False
    mlc_sent = True
    mouse_left_released = False
    ser.write(f"C,1\n".encode())
    if log_key_presses:
        print("Left mouse button pressed")

def on_right_click():
    global mrc_sent, mrcr_sent, mouse_right_click, mouse_right_released
    mouse_right_click = True
    mrcr_sent = False
    mouse_right_released = False
    mrc_sent = True
    ser.write(f"C,3\n".encode())
    if log_key_presses:
        print("Right mouse button clicked")

def on_left_release():

    global mlc_sent, mlcr_sent, mouse_left_click, mouse_left_released
    mouse_left_released = True
    mlc_sent = False
    mouse_left_click = False
    mlcr_sent = True
    ser.write(f"C,2\n".encode())
    if log_key_presses:
        print("Left mouse button released")

def on_right_release():
    global mrc_sent, mrcr_sent, mouse_right_click, mouse_right_released
    mouse_right_released = True
    mrc_sent = False
    mouse_right_click = False
    mrcr_sent = True
    ser.write(f"C,4\n".encode())
    if log_key_presses:
        print("Right mouse button released")
        
def main():
    global ser, tk, microprocessor_port, host_system, target_system, isSpecialKeyPressed, special_keys_pressed, special_keys, keyboard_wait, off_system, last_keys_pressed, log_mouse_movement, log_key_presses, log_operational_messages, log_microcontroller_messages
    global mlc_sent, mrc_sent, mlcr_sent, mrcr_sent  # Declare these as global to modify them inside the functions


    microprocessor_port = find_microprocessor_port()

    ser = serial.Serial(microprocessor_port, 1000000, timeout=1, write_timeout=2)

    if microprocessor_port is None:
        print("Microcontroller not found. Please check the connection.")
        return
    else :
        if log_microcontroller_messages:
            print(f"Connected to microcontroller on {microprocessor_port}")
        
    try:

        hide_icon()  # Start with the icon hidden

        mouse.hook(handleMouseClick)

        # Start the Flask server in a new thread
        flask_thread = threading.Thread(target=start_flask)
        flask_thread.daemon = True  # Ensures the thread will close when the main program exits
        flask_thread.start()

        while True:
            check_position()
            time.sleep(0.02)

    except Exception as e:
        print(f"Error occurred during setup: {e}")
        pass


if __name__ == "__main__":

    main()
