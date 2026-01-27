import time
import board
import microcontroller
import digitalio
import rtc
import usb_hid
import gc

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

# Map ASCII char to segments bitmap.
FONT = {
    ord("0"): 0b0111111,
    ord("1"): 0b0000110,
    ord("2"): 0b1011011,
    ord("3"): 0b1001111,
    ord("4"): 0b1100110,
    ord("5"): 0b1101101,
    ord("6"): 0b1111101,
    ord("7"): 0b0000111,
    ord("8"): 0b1111111,
    ord("9"): 0b1101111,
    ord(" "): 0b0000000,
    ord("A"): 0b1110111,
    ord("B"): 0b1111100,
    ord("C"): 0b1011000,
    ord("D"): 0b1011110,
    ord("E"): 0b1111001,
    ord("F"): 0b1110001,
    ord("G"): 0b0111101,
    ord("H"): 0b1110100,
    ord("I"): 0b0000100,
    ord("J"): 0b0011110,
    ord("K"): 0b1110101,
    ord("L"): 0b0111000,
    ord("N"): 0b1010100,
    ord("O"): 0b1011100,
    ord("P"): 0b1110011,
    ord("Q"): 0b1100111,
    ord("R"): 0b1010000,
    ord("S"): 0b1101100,
    ord("T"): 0b1111000,
    ord("U"): 0b0011100,
    ord("V"): 0b0111110,
    ord("X"): 0b1110110,
    ord("Y"): 0b1101110,
    ord("Z"): 0b0011011,
    ord("-"): 0b1000000,
    ord("_"): 0b0001000,
    ord("\""): 0b0100010,
    ord("!"): 0b1101011,
    ord("?"): 0b1010011,
    ord("="): 0b1001000,
    ord("^"): 0b0100011,
    ord("("): 0b0111001,
    ord(")"): 0b0001111,
    ord(":"): 0b0001001,
    ord(";"): 0b0000101,
    ord("["): 0b0111001,
    ord("]"): 0b0001111,
    ord("{"): 0b1000110,
    ord("}"): 0b1110000,
    ord("<"): 0b1100001,
    ord(">"): 0b1000011,
    ord("/"): 0b1010010,
    ord("\\"): 0b1100100,
    ord("~"): 0b1010010,
    ord("@"): 0b1111011,
    ord("`"): 0b1100000,
    # MacCyrillic (тому що можу!)
    0x80: 0b1110111, # 'А'
    0x81: 0b1111101, # 'Б'
    0x82: 0b1111111, # 'В'
    0x83: 0b0110011, # 'Г'
    0x84: 0b1101111, # 'Д'
    0x85: 0b1111001, # 'Е'
    0x87: 0b0001111, # 'З'
    0x88: 0b0011100, # 'И'
    0x89: 0b0011101, # 'Й'
    0x8A: 0b1110101, # 'К'
    0x8B: 0b1010110, # 'Л'
    0x8C: 0b0100111, # 'М' (right part)
    0x8D: 0b1110110, # 'Н'
    0x8E: 0b1011100, # 'О'
    0x8F: 0b0110111, # 'П'
    0x90: 0b1110011, # 'Р'
    0x91: 0b0111001, # 'С'
    0x92: 0b0110001, # 'Т' (right part)
    0x93: 0b1101110, # 'У'
    0x96: 0b1101010, # 'Ц'
    0x97: 0b1100110, # 'Ч'
    0x98: 0b0111100, # 'Ш' (left part)
    0x99: 0b1100010, # 'Щ' (left part)
    0x9A: 0b0000001, # 'Ъ' (left part)
    0x9C: 0b1111100, # 'Ь'
    0x9D: 0b1001111, # 'Э'
    0x9F: 0b1010111, # 'Я'
    0xDF: 0b1010111, # 'я'
    0xA1: 0b1100011, # '˚'
    0xA2: 0b1010010, # 'Ґ'
    0xB6: 0b1010010, # 'ґ'
    0xA6: 0b1100111, # '¶'
    0xA7: 0b0110000, # 'І'
    0xB4: 0b0110000, # 'і'
    0xAB: 0b1100101, # 'Ђ'
    0xAC: 0b1100101, # 'ђ'
    0xCB: 0b1110101, # 'Ћ'
    0xCC: 0b1110101, # 'ћ'
    0xAE: 0b1010001, # 'Ѓ'
    0xAF: 0b1010001, # 'ѓ'
    0xB2: 0b1101001, # '≤'
    0xB3: 0b1001011, # '≥'
    0xB5: 0b1110010, # 'µ'
    0xB7: 0b0001110, # 'Ј'
    0xC0: 0b0001110, # 'ј'
    0xB8: 0b1111001, # 'Є'
    0xB9: 0b1111001, # 'є'
    0xBA: 0b0010001, # 'Ї'
    0xBB: 0b0010001, # 'ї'
    0xC1: 0b1101101, # 'Ѕ'
    0xCF: 0b1101101, # 'ѕ'
    0xC2: 0b0000011, # '¬'
    0xC3: 0b0011110, # '√'
    0xCD: 0b1011001, # 'Ќ'
    0xCE: 0b1011001, # 'ќ'
    0xD2: 0b0100010, # '“'
    0xD3: 0b0100010, # '”'
    0xD4: 0b0000010, # '‘'
    0xD5: 0b0100000, # '’'
    0xD7: 0b0010100, # '„'
    0xD8: 0b1001101, # 'Ў'
    0xD9: 0b1001101, # 'ў'
    0xDA: 0b1101010, # 'Џ'
    0xDB: 0b1101010, # 'џ'
    0xDD: 0b1011001, # 'Ё'
    0xDE: 0b1011001, # 'ё'
    0xFF: 0b1111001, # '€'
}

REPLACE = {
    ord("%"): (0xA1, ord("O")), # % → °o
    ord("+"): (ord("{"), ord("}")), # + → {}
    ord("M"): (0x83, 0x8C), # M → ГМ
    ord("W"): (0x98, 0xC3), # W → Ш√
    0x86: (0x9D, 0xB8), # Ж → ЭЄ
    0x8C: (0x83, 0x8C), # М → ГМ
    0x92: (ord("7"), 0x92), # Т → 7Т
    0x94: (0xA6, 0x90), # Ф → ¶Р
    0x95: (ord("]"), ord("[")), # Х → ][
    0x98: (0x98, 0xC3), # Ш → Ш√
    0x99: (0x99, 0x97), # Щ → ЩЧ
    0x9A: (0x9A, 0x9C), # Ъ → ЪЬ
    0x9B: (0x9C, ord("1")), # Ы → Ь1
    0x9E: (ord("}"), ord("0")), # Ю → }0
    0xA8: (ord("("), ord("R"), ord(")")), # ® → (R)
    0xA9: (ord("("), ord("C"), ord(")")), # © → (C)
    0xB0: (ord("O"), ord("O")), # ∞ → oo
    0xBC: (0x92, 0x9C), # Љ → ТЬ
    0xBD: (0x92, 0x9C), # љ → ТЬ
    0xBE: (ord("}"), 0x9C), # Њ → }Ь
    0xBF: (ord("}"), 0x9C), # њ → }Ь
    0xD0: (ord("-"), ord("-")), # — → --
    0xD1: (ord("-"), ord("-"), ord("-")), # – → ---
    0xDC: (ord("n"), ord("o")), # № → no
}

# Map symbol to segment and digit.
TOTAL_SYMBOLS = 3 * 4

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
CMD_SET_TEXT  = 0x10
CMD_SET_TIME  = 0x12
CMD_SHOW_TIME = 0x13
CMD_SET_RAW   = 0x14

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

display_buffer_offset = 0
display_buffer_len = 0
display_buffer_capacity = 48 * 3
display_buffer = [255 for _ in range(display_buffer_capacity)]

scroll_last_time = time.monotonic()
scroll_delta = 0.5

display_time = True
time_last_update = time.monotonic()
time_update_delta = 1.0
time_show_dots = False

display_raw = False
raw_segments = [0, 0, 0, 0]
raw_symbols = 0  # bitmap for 12 additional symbols


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

def display_segments_byte(position: int, segments_byte: int):
    disable_all_segments_and_digits()

    for i in range(7):
        write_segment(i, segments_byte & (1 << i))

    write_digit(position, True)

def display_char(position: int, char: int):    # Convert lowercase to uppercase.
    # All unknown characters will be replaced with spaces.
    display_segments_byte(position, FONT.get(char, 0))

def display_symbol(symbol: int):
    if symbol not in SYMBOLS:
        return

    disable_all_segments_and_digits()

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
    global display_buffer, display_buffer_offset, display_buffer_len, display_time, scroll_last_time, display_raw, raw_segments, raw_symbols

    if usb_hid_device is None:
        return

    report = usb_hid_device.get_last_received_report()
    if not report:
        return

    display_buffer[0] = 0x00
    display_buffer_offset = 0
    display_buffer_len = 0

    if report[0] == CMD_SET_TEXT:
        for byte in report[1:]:
            if byte == 0:
                break

            if 97 <= byte and byte <= 122:
                byte = byte - 32
            if 0xE0 <= byte and byte <= 0xFE:
                byte = byte - 0x60


            ligature = REPLACE.get(byte, (byte,))
            for glyph in ligature:
                display_buffer[display_buffer_len] = glyph
                display_buffer_len += 1
        
        if display_buffer_len > 0:
            # Hide time and reset scroll timer (with small delay at first letter)
            display_time = False
            display_raw = False
            scroll_last_time = time.monotonic() + 0.5

    elif report[0] == CMD_SET_TIME:
        timestamp = int.from_bytes(report[1:], byteorder='little')
        rtc.RTC().datetime = time.localtime(timestamp)

        display_raw = False
        display_time = True

    elif report[0] == CMD_SHOW_TIME:
        display_raw = False
        display_time = True

    elif report[0] == CMD_SET_RAW:
        raw_segments[0] = report[1]
        raw_segments[1] = report[2]
        raw_segments[2] = report[3]
        raw_segments[3] = report[4]

        raw_symbols = report[5] | (report[6] << 8)

        display_time = False
        display_raw = True


#
# MAIN
#

def show_text():
    global display_buffer, display_buffer_offset, display_buffer_len

    start = display_buffer_offset

    end = display_buffer_offset + DISPLAY_SIZE
    if end > display_buffer_len:
        end = display_buffer_len

    for i in range(start, end):
        display_char(i - display_buffer_offset, display_buffer[i])
        time.sleep(0.001)
    
    if display_time and time_show_dots:
        display_symbol(Symbol.TOP_DOT)
        time.sleep(0.001)

        display_symbol(Symbol.BOTTOM_DOT)
        time.sleep(0.001)

    disable_all_segments_and_digits()

def show_raw():
    global raw_segments, raw_symbols

    for i in range(DISPLAY_SIZE):
        display_segments_byte(i, raw_segments[i])
        time.sleep(0.001)

    for symbol_id in range(TOTAL_SYMBOLS):
        if raw_symbols & (1 << symbol_id):
            display_symbol(symbol_id)
            time.sleep(0.001)

    disable_all_segments_and_digits()

def update_time():
    global display_buffer, display_buffer_len, time_last_update, time_update_delta, time_show_dots

    now = time.monotonic()
    if time_update_delta > now - time_last_update:
        return

    time_show_dots = not time_show_dots

    localtime = time.localtime()

    hour = localtime.tm_hour
    min = localtime.tm_min

    zero = ord('0')
    display_buffer[0] = zero + (hour // 10)
    display_buffer[1] = zero + (hour % 10)
    display_buffer[2] = zero + (min // 10)
    display_buffer[3] = zero + (min % 10)

    display_buffer_len = 4
    time_last_update = now

def scroll_text():
    global display_buffer_offset, display_buffer_len, scroll_last_time, display_time

    now = time.monotonic()
    if now - scroll_last_time >= scroll_delta:
        if display_buffer_len > DISPLAY_SIZE:
            display_buffer_offset += 1

        if display_buffer_offset > display_buffer_len:
            # Forgetting the message
            display_buffer_offset = 0
            display_buffer_len = 0
            display_time = True

        scroll_last_time = now

while True:
    gc.disable()
    scan_keyboard()

    for key, is_pressed in keys_pressed.items():
        if is_pressed and not keys_last_pressed[key]:
            usb_hid_send_key(key)

    usb_hid_poll_reports()

    if display_raw:
        show_raw()
    elif display_time:
        update_time()
        show_text()
    else:
        show_text()
        scroll_text()

    gc.enable()
    gc.collect()
