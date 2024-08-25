import serial
import serial.tools.list_ports
import pyautogui
import mouse
import time
import keyboard
from screeninfo import get_monitors


def find_arduino_port():
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
    global off_system, last_keys_pressed  # Declare global variables here

    arduino_port = find_arduino_port()

    if arduino_port is None:
        print("Arduino not found. Please check the connection.")
        return

    try:
        ser = serial.Serial(arduino_port, 9600, timeout=1)
        print(f"Connected to Arduino on {arduino_port}")

        monitors = get_monitors()
        right_monitor = max(monitors, key=lambda m: m.x)

        # Host computer's screen dimensions
        host_width = right_monitor.width
        host_height = right_monitor.height

        # Target computer's screen dimensions (e.g., MacBook Air M2 Retina)
        target_width = 2560  # Width of the target computer's screen
        target_height = 1600  # Height of the target computer's screen

        edge_threshold = 10
        off_system = False
        last_keys_pressed = set()  # Initialize the set

        def scale_to_signed_byte(value, max_value):
            # Scale the value to fit within the range of -128 to 127
            scaled_value = int((value / max_value) * 127)
            return scaled_value

        def scale_to_byte(value, max_value):
            return int((value / max_value) * 255)

        def scale_movement(value, host_max, target_max):
            """Scale movement from host screen size to target screen size."""
            return int((value / host_max) * target_max)

        def move_to_relative(x, y):
            absolute_x = right_monitor.x + x
            absolute_y = right_monitor.y + y
            mouse.move(absolute_x, absolute_y)
            print(f"Moved cursor to relative x={x}, y={y} on rightmost monitor")

        while True:
            try:
                if ser.in_waiting > 0:
                    incoming_data = ser.readline().decode("utf-8").strip()
                    print(f"Received from Arduino: {incoming_data}")

                x, y = mouse.get_position()
                print(f"Mouse position: x={x}, y={y} | Off-system: {off_system}")

                if right_monitor.y <= y <= right_monitor.y + host_height:
                    if (
                        x >= right_monitor.x + host_width - edge_threshold
                        and not off_system
                    ):
                        off_system = True
                        print("Switching to target system...")
                        mouse.move(right_monitor.x, y)
                        time.sleep(0.1)
                        ser.write(b"M")
                        scaled_y = scale_movement(
                            y - right_monitor.y, host_height, target_height
                        )
                        x_value = scale_to_signed_byte(right_monitor.x, target_width)
                        y_value = scale_to_signed_byte(scaled_y, target_height)
                        ser.write(f"{x_value},{y_value}\n".encode())

                    elif x <= right_monitor.x + edge_threshold and off_system:
                        off_system = False
                        print("Switching back to host system...")
                        move_to_relative(host_width - 2, y - right_monitor.y)
                        time.sleep(0.1)
                        ser.write(b"S")

                if off_system:
                    print(f"Mouse position: x={x}, y={y} | Off-system: {off_system}")
                    scaled_x = scale_movement(
                        x - right_monitor.x, host_width, target_width
                    )
                    scaled_y = scale_movement(
                        y - right_monitor.y, host_height, target_height
                    )
                    x_value = scale_to_signed_byte(x, host_width)
                    y_value = scale_to_signed_byte(y, host_height)

                    current_keys_pressed = {
                        char
                        for char in "abcdefghijklmnopqrstuvwxyz1234567890{\}[]\\|;:'\",<.>/?!@#$%^&*()-=_+~`"
                        if keyboard.is_pressed(char)
                    }
                    new_keys_pressed = current_keys_pressed - last_keys_pressed
                    last_keys_pressed = current_keys_pressed

                    for key in new_keys_pressed:
                        ser.write(f"K,{key}\n".encode())

                    if mouse.is_pressed("left"):
                        ser.write(f"C,1\n".encode())
                    elif mouse.is_pressed("right"):
                        ser.write(f"C,2\n".encode())
                    elif len(new_keys_pressed) > 0:
                        for key in new_keys_pressed:
                            ser.write(f"K,{key}\n".encode())
                    else:
                        print(f"Sending x={x_value}, y={y_value}")
                        ser.write(f"M{x},{y}\n".encode())

                time.sleep(0.01)
            except Exception as e:
                print(f"Error occurred in loop: {e}")
                break

    except Exception as e:
        print(f"Error occurred during setup: {e}")


if __name__ == "__main__":
    main()
