import serial
import serial.tools.list_ports
import pyautogui
import mouse
import time
import keyboard
from screeninfo import get_monitors

# Global variables
mouse_left_click = False
mouse_right_click = False
mouse_left_released = False
mouse_right_released = False

# Track sent mouse actions
mlc_sent = False  # Left click sent
mrc_sent = False  # Right click sent
mlcr_sent = False  # Left click released sent
mrcr_sent = False  # Right click released sent


def find_microprocessor_port():
    ports = list(serial.tools.list_ports.comports())
    for port in ports:
        if (
            any(
                keyword in port.description
                for keyword in ["Leonardo", "Pro Micro", "Uno", "Mega", "Arduino"]
            )
            or port.device == "COM24"
        ):
            return port.device
    return None


def main():
    global off_system, last_keys_pressed, log_mouse_movement, log_key_presses, log_operational_messages, log_microcontroller_messages, shift_logged
    global mlc_sent, mrc_sent, mlcr_sent, mrcr_sent  # Declare these as global to modify them inside the functions

    log_microcontroller_messages = False
    log_operational_messages = True
    log_mouse_movement = False
    log_key_presses = True
    shift_logged = False

    microprocessor_port = find_microprocessor_port()

    if microprocessor_port is None:
        print("Microcontroller not found. Please check the connection.")
        return

    try:
        ser = serial.Serial(microprocessor_port, 9600, timeout=1, write_timeout=2)
        if log_microcontroller_messages:
            print(f"Connected to microcontroller on {microprocessor_port}")

        shift_pressed = False
        two_or_more_keys_pressed = False
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
            if not mlc_sent:
                mouse_left_click = True
                mlcr_sent = False
                mlc_sent = True
                mouse_left_released = False
                ser.write(f"C,1\n".encode())
                if log_key_presses:
                    print("Left mouse button pressed")

        def on_right_click():
            global mrc_sent, mrcr_sent, mouse_right_click, mouse_right_released  # Global declaration
            if not mrc_sent:
                mouse_right_click = True
                mrcr_sent = False
                mouse_right_released = False
                mrc_sent = True
                ser.write(f"C,2\n".encode())
                if log_key_presses:
                    print("Right mouse button clicked")

        def on_left_release():
            global mlc_sent, mlcr_sent, mouse_left_click, mouse_left_released  # Global declaration
            if not mlcr_sent:
                mouse_left_released = True
                mlc_sent = False
                mouse_left_click = False
                mlcr_sent = True
                ser.write(f"C,3\n".encode())
                if log_key_presses:
                    print("Left mouse button released")

        def on_right_release():
            global mrc_sent, mrcr_sent, mouse_right_click, mouse_right_released  # Global declaration
            if not mrcr_sent:
                mouse_right_released = True
                mrc_sent = False
                mouse_right_click = False
                mrcr_sent = True
                ser.write(f"C,4\n".encode())
                if log_key_presses:
                    print("Right mouse button released")

        # Register mouse event handlers
        mouse.on_button(on_left_click, args=(), buttons="left", types="down")
        mouse.on_button(on_right_click, args=(), buttons="right", types="down")
        mouse.on_button(on_left_release, args=(), buttons="left", types="up")
        mouse.on_button(on_right_release, args=(), buttons="right", types="up")

        while True:
            try:
                if ser.in_waiting > 0:
                    incoming_data = ser.readline().decode("utf-8").strip()
                    if log_microcontroller_messages:
                        print(f"Received from microcontroller: {incoming_data}")

                x, y = mouse.get_position()

                if log_mouse_movement:
                    print(f"Mouse position: x={x}, y={y} | Off-system: {off_system}")

                if right_monitor.y <= y <= right_monitor.y + host_height:
                    if (
                        x >= right_monitor.x + host_width - edge_threshold
                        and not off_system
                    ):
                        off_system = True
                        if log_operational_messages:
                            print("Switching to target system...")

                        mouse.move(right_monitor.x - 10000, y)  # Move cursor off-screen
                        time.sleep(0.1)

                    elif x <= right_monitor.x + edge_threshold and off_system:
                        off_system = False
                        if log_operational_messages:
                            print("Switching back to host system...")

                        move_to_relative(host_width - 2, y - right_monitor.y)
                        time.sleep(0.2)

                if off_system:

                    if not shift_pressed:

                        current_keys_pressed = {
                            char
                            for char in (
                               "abcdefghijklmnopqrstuvwxyz1234567890`-=[];',./"
                            )
                            if keyboard.is_pressed(char)
                        }
                    else:
                        current_keys_pressed = {
                            char
                            for char in (
                                '~!@#$%^&*()_+{}|:"<>?'
                            )
                            if keyboard.is_pressed(char)
                        }

                    new_keys_pressed = current_keys_pressed - last_keys_pressed
                    last_keys_pressed = current_keys_pressed

                    if len(new_keys_pressed) > 0:
                        for key in new_keys_pressed:
                            if log_key_presses:
                                print(f"Key pressed: {key}")
                            ser.write(f"K,{key}\n".encode())
                    else:
                        if log_mouse_movement:
                            print(f"Sending x={x}, y={y}")
                        ser.write(f"M{x},{y}\n".encode())

                time.sleep(0.01)
            except TimeoutError as e:
                print(f"Timeout error occurred: {e}")
                pass
            except serial.SerialTimeoutException:
                print(f"Serial timeout occurred")
                pass  # Ignore the SerialTimeoutException and continue running
            except Exception as e:
                print(f"Error occurred in loop: {e}")
                break

    except Exception as e:
        print(f"Error occurred during setup: {e}")


if __name__ == "__main__":
    try:
        main()
    except TimeoutError as e:
        pass  # Handle the TimeoutError or simply ignore it
