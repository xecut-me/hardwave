import time
import board
import microcontroller
import digitalio
import usb_hid

from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode


#
# CONSTS
#

DISPLAY_SIZE = 4

DIGIT_PINS = [
    board.P0_29, board.P0_31, board.P1_13, board.P1_15
]

SEGMENT_PINS = [
    board.P1_06, board.P1_04, board.P0_11, board.P1_00,
    board.P0_24, board.P0_22, board.P0_20, board.P0_17,
    board.P0_08, board.P0_06
]

KEYBOARD_ROWS = 8

KEYBOARD_COLUMNS_PINS = [
    board.P0_09, board.P0_10, board.P1_11
]

# Map ASCII char to segments.
FONT = {
    ord("0"): [0,1,2,3,4,5],
    ord("1"): [1,2],
    ord("2"): [0,1,3,4,6],
    ord("3"): [0,1,2,3,6],
    ord("4"): [1,2,5,6],
    ord("5"): [0,2,3,5,6],
    ord("6"): [0,2,3,4,5,6],
    ord("7"): [0,1,2],
    ord("8"): [0,1,2,3,4,5,6],
    ord("9"): [0,1,2,3,5,6],
    ord(" "): [],
    ord("A"): [0,1,2,4,5,6],
    ord("B"): [2,3,4,5,6],
    ord("C"): [3,4,6],
    ord("D"): [1,2,3,4,6],
    ord("E"): [0,3,4,5,6],
    ord("F"): [0,4,5,6],
    ord("G"): [0,2,3,4,5],
    ord("H"): [2,4,5,6],
    ord("I"): [2],
    ord("J"): [1,2,3,4],
    ord("K"): [0,2,4,5,6],
    ord("L"): [3,4,5],
    ord("M"): [0,1,2,4,5],
    ord("N"): [2,4,6],
    ord("O"): [2,3,4,6],
    ord("P"): [0,1,4,5,6],
    ord("Q"): [0,1,2,5,6],
    ord("R"): [4,6],
    ord("S"): [2,3,5,6],
    ord("T"): [3,4,5,6],
    ord("U"): [2,3,4],
    ord("V"): [1,2,3,4,5],
    ord("W"): [1,2,3,4,5,6],
    ord("X"): [1,2,4,5,6],
    ord("Y"): [1,2,3,5,6],
    ord("Z"): [0,1,3,4],
    ord("-"): [6],
    ord("_"): [3],
}

# Map symbol to segment and digit.
class Symbol:
    TOP_DOT = 0
    BOTTOM_DOT = 1
    CIRCLE = 2
    WAVES = 3
    WEIGHT = 4
    SPIRAL = 5
    CELSIUS = 6
    TEN_DOT_ONE = 7
    FAN = 8
    KG = 9
    RHOMBUS = 10
    STARS = 11

SYMBOLS = {
    Symbol.TOP_DOT:     (7,0),
    Symbol.BOTTOM_DOT:  (7,1),
    Symbol.CELSIUS:     (7,2),
    Symbol.KG:          (7,3),
    Symbol.CIRCLE:      (8,0),
    Symbol.WEIGHT:      (8,1),
    Symbol.TEN_DOT_ONE: (8,2),
    Symbol.RHOMBUS:     (8,3),
    Symbol.WAVES:       (9,0),
    Symbol.SPIRAL:      (9,1),
    Symbol.FAN:         (9,2),
    Symbol.STARS:       (9,3),
}

# Map keyboard (row, column) to USB HID Keycode.
class Key:
    COOK     = (6, 2)
    DEFROST  = (5, 2)
    REHEAT   = (4, 0)
    WAVES    = (3, 1)
    TIME     = (5, 1)
    ELEMENTS = (6, 1)
    PLUS     = (2, 2)
    MINUS    = (1, 2)
    TEN_MIN  = (7, 0)
    ONE_MIN  = (6, 0)
    TEN_SEC  = (5, 0)
    STOP     = (7, 1)
    START    = (4, 1)

    ALL_KEYS = [COOK, DEFROST, REHEAT, WAVES, TIME, ELEMENTS, PLUS, MINUS, TEN_MIN, ONE_MIN, TEN_SEC, STOP, START]

KEYCODES = {
    Key.COOK: Keycode.C,
    Key.DEFROST: Keycode.D,
    Key.REHEAT: Keycode.R,
    Key.WAVES: Keycode.W,
    Key.TIME: Keycode.T,
    Key.ELEMENTS: Keycode.E,
    Key.PLUS: Keycode.KEYPAD_PLUS,
    Key.MINUS: Keycode.KEYPAD_MINUS,
    Key.TEN_MIN: Keycode.Z,
    Key.ONE_MIN: Keycode.Y,
    Key.TEN_SEC: Keycode.X,
    Key.STOP: Keycode.ESCAPE,
    Key.START: Keycode.ENTER,
}

# USB HID consts.
CMD_KEY = 0x01
CMD_SET_TIME = 0x10
CMD_SET_TEXT = 0x12
CUSTOM_HID_REPORT_ID = 0x04


#
# DEVICE STATE
#

keys_last_pressed = {key: False for key in Key.ALL_KEYS}
keys_pressed = {key: False for key in Key.ALL_KEYS}

usb_hid_device = next(
    d
    for d in usb_hid.devices
    if getattr(d, "usage_page", None) == 0xFF00 and getattr(d, "usage", None) == 0x01
)
usb_keyboard = Keyboard(usb_hid.devices)

display_text_offset = 0
display_buffer_size = 0
display_buffer_max_size = 48
display_buffer = [255 for _ in range(display_buffer_max_size)]


#
# HELPERS
#

def pin_output(p: microcontroller.Pin) -> digitalio.DigitalInOut:
    p = digitalio.DigitalInOut(p)
    p.direction = digitalio.Direction.OUTPUT
    p.value = True  # inverted
    return p

def pin_input(p: microcontroller.Pin) -> digitalio.DigitalInOut:
    p = digitalio.DigitalInOut(p)
    p.direction = digitalio.Direction.INPUT
    p.pull = digitalio.Pull.UP
    return p


#
# HARDWARE CONTROL
#

digits = [pin_output(pin) for pin in DIGIT_PINS]
segments = [pin_output(pin) for pin in SEGMENT_PINS]

def write_digit(i: int, state: bool):
    digits[i].value = not state

def write_segment(i: int, state: bool):
    segments[i].value = state if i >= 8 else not state

def disable_all_segments_and_digits():
    for i in range(len(digits)):
        write_digit(i, False)

    for i in range(len(segments)):
        write_segment(i, False)

#
# DISPLAY CONTROL
#

def show_char(position: int, char: int):
    if position > 3:
        return

    disable_all_segments_and_digits()

    # Convert lowercase to uppercase.
    if 97 <= char and char <= 122:
        char = char - 32

    # All unknown characters will be replaced with spaces.
    for i in FONT.get(char, []):
        write_segment(i, True)

    write_digit(position, True)

def show_symbol(symbol: int):
    disable_all_segments_and_digits()

    if symbol not in SYMBOLS:
        return

    segment, digit = SYMBOLS[symbol]

    write_segment(segment, True)
    write_digit(digit, True)


#
# KEYBOARD SCANNER
#

keyboard_columns = [pin_input(pin) for pin in KEYBOARD_COLUMNS_PINS]

def save_pressed():
    for key, is_pressed in keys_pressed.items():
        keys_last_pressed[key] = is_pressed

def scan_keyboard():
    disable_all_segments_and_digits()

    save_pressed()

    for row in range(KEYBOARD_ROWS):
        write_segment(row, True)

        for col, pin in enumerate(keyboard_columns):
            key = (row, col)

            key_pressed = not pin.value
            if key_pressed:
                keys_pressed[key] = True
            elif key in keys_pressed:
                keys_pressed[key] = False

        write_segment(row, False)


#
# USB HID
#

def usb_hid_send_key(key: tuple[int, int]):
    code = KEYCODES.get(key,None)
    if code is not None:
        usb_keyboard.send(code)

def usb_hid_poll_reports():
    if usb_hid_device is None:
        return

    report = usb_hid_device.get_last_received_report()
    if not report:
        return

    display_buffer_size = 0

    for byte in report:
        if byte == 0:
            break

        display_buffer[display_buffer_size] = byte
        display_buffer_size += 1


#
# MAIN
#

def show_text():
    for pos in range(DISPLAY_SIZE):
        i = display_text_offset + pos
        if i < len(display_buffer):
            show_char(pos, display_buffer[i])
            time.sleep(0.001)

    # Hide last character.
    disable_all_segments_and_digits()

while True:
    scan_keyboard()

    for key, is_pressed in keys_pressed.items():
        if is_pressed and not keys_last_pressed[key]:
            usb_hid_send_key(key)

    usb_hid_poll_reports()

    show_text()
