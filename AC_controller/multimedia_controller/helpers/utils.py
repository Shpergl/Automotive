from multimedia_controller.constants import AC_FAN_DIR, AC_TEMP
from multimedia_controller.settings import AC_LOWEST_TEMP, AC_HIGHEST_TEMP

state_to_fan_dir_map = {
    1: AC_FAN_DIR.AC_FAN_DIR_DOWN,
    2: AC_FAN_DIR.AC_FAN_DIR_CENTER,
    3: AC_FAN_DIR.AC_FAN_DIR_DOWN_AND_CENTER,
    4: AC_FAN_DIR.AC_FAN_DIR_UP,
    5: AC_FAN_DIR.AC_FAN_DIR_UP_AND_DOWN,
    6: AC_FAN_DIR.AC_FAN_DIR_CENTER_AND_UP,
    7: AC_FAN_DIR.AC_FAN_DIR_UP_DOWN_CENTER,
}

fan_dir_to_state_map = {v: k for k, v in state_to_fan_dir_map.items()}


def pack_fan_dir(up, middle, down):
    dir_state = [up, middle, down]
    resulted_state = int("".join(str(i) for i in dir_state), 2)
    return state_to_fan_dir_map[resulted_state]


def unpack_fan_dir(state):
    resulted_state = fan_dir_to_state_map[state]
    return [int(x) for x in '{0:03b}'.format(resulted_state)]


def scale(old_range, new_range, old_value):
    return int(((old_value - min(old_range)) * (max(new_range) - min(new_range)) /
                (max(old_range) - min(old_range))) + min(new_range))


def chunk_string(string, length):
    return [string[0+i:length+i] for i in range(0, len(string), length)]


def ascii_to_hex(char):
    return int('0x{:x}'.format(ord(char)), 16)


def get_16_bit_hex(hex1, hex2):
    return int(hex1) * 256 + int(hex2)


def get_24_bit_hex(hex1, hex2, hex3):
    return hex3 + (hex2 << 8) + (hex1 << 16)


def round_float(value):
    return round(value*2)/2


def convertGuiTemp(value):
    if value == AC_TEMP.AC_TEMP_LO:
        return AC_LOWEST_TEMP
    elif value == AC_TEMP.AC_TEMP_HI:
        return AC_HIGHEST_TEMP
    return max(AC_LOWEST_TEMP, min(AC_HIGHEST_TEMP, AC_LOWEST_TEMP + (value-1) * 0.5))

