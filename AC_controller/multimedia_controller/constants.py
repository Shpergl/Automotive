
# UART Pockets
class UART_TYPES:
    AC = 0x03  # HU -> CH_CMD_AIR_CONDITIONING_INFO
    CH_CMD_ILL_INFO = 0x04  # HU -> CH_CMD_ILL_INFO
    CH_CMD_PARKING_RADAR_SWITCH_INFO = 0x07
    R_PARK = 0x22  # HU -> CH_CMD_REAR_RADAR_INFO
    F_PARK = 0x23  # HU -> CH_CMD_FRONT_RADAR_INFO
    DOOR = 0x24  # HU -> CH_CMD_BASE_INFO
    PARK_ON = 0x25
    TMPS = 0x65  # HU -> CH_CMD_TPMS_INFO

    CH_CMD_VEHICLE_SPEED_SIGNAL = 0x0b

class CONTROLLER_NAMES:
    TEMP = 'TempController'


class CAN_COMMANDS_IDS:
    SPA_DISTANCE = 0x439
    DOOR_STATUS = 0x320
    OUTSIDE_TEMP = 0x7a0

    TRIONIC_DATA_INIT = 0x220
    TRIONIC_DATA_REPLY = 0x238
    TRIONIC_DATA_QUERY = 0x240
    TRIONIC_DATA_QUERY_REPLY = 0x258
    TRIONIC_REPLY_ACK = 0x266

    PEDALS_REVERSE_GEAR = 0x280
    STEERING_WHEEL_SID_BUTTONS = 0x290

    SID_AUDIO_TEXT = 0x328
    ACC_TO_SID_TEXT = 0x32c  # Automatic air conditioning
    TWICE_TO_SID_TEXT = 0x32f
    SPA_TO_SID_TEXT = 0x337  # Park assistant
    ACC_TO_SID_TEXT_CONTROL = 0x34c
    TWICE_TO_SID_TEXT_CONTROL = 0x34f
    SPA_TO_SID_TEXT_CONTROL = 0x357

    SID_TEXT_PRIORITY = 0x368
    AUDIO_RDS_STATUS = 0x380
    HEAD_LIGHTS = 0x3b0
    CD_CHANGER_CONTROL = 0x3c0
    CD_CHANGER_INFO = 0x3c8
    AUTOMATIC_GEARBOX = 0x3e0
    LIGHT_DIMMER_LIGHT_SENSOR = 0x410

    SID_BEEP_REQUEST = 0x430

    ENGINE_RPM_AND_SPEED = 0x460
    STREERING_WHEEL_AND_VIN = 0x4a0

    ACC_AND_INSIDE_TEMP = 0x520
    ACC = 0x530
    SEAT_MEMORY = 0x590

    COOLANT_TEMP_AIR_PRESSURE = 0x5c0
    FUEL_USAGE = 0x630
    MILEAGE = 0x640
    AUDIO_HEAD_UNIT = 0x6a1
    CD_CHANGER = 0x6a2
    RDS_TIME = 0x720

    CLOCK = 0x730

    SECURITY = 0x740
    SECURITY_2 = 0x750


CAN_COMMANDS_NAMES = {v: k for k, v in CAN_COMMANDS_IDS.__dict__.items() if not k.startswith('_')}


class UART_COMMANDS:
    AC_ON = b'\x2e\xe0\x02\x17\x01\x05'
    AC_STATUS_ON = b'\x2e\xe0\x02\x01\x01\x1b'
    AC_MODE_AUTO_ON = b'\x2e\xe0\x02\x15\x01\x07'
    CYCLE_MODE_ON = b'\x2e\xe0\x02\x19\x01\x03'
    DUAL_MODE_ON = b'\x2e\xe0\x02\x10\x01\x0c'

    L_SEAT_HEAT_SWITCH = b'\x2e\xe0\x02\x0b\x01\x11'
    R_SEAT_HEAT_SWITCH = b'\x2e\xe0\x02\r\x01\x0f'
    L_SEAT_FAN_SWITCH = b'\x2e\xe0\x02\x0c\x01\x10'
    R_SEAT_FAN_SWITCH = b'\x2e\xe0\x02\x0e\x01\x0e'

    FAN_DIR_WINDOW = b'\x2e\xe0\x02\x12\x01\n'
    FAN_DIR_MIDDLE = b'\x2e\xe0\x02\x07\x01\x15'
    FAN_DIR_DOWN = b'\x2e\xe0\x02\x08\x01\x14'
    FAN_SPEED_INC = b'\x2e\xe0\x02\n\x01\x12'
    FAN_SPEED_DEC = b'\x2e\xe0\x02\t\x01\x13'

    WINDOW_MAX_ON = b'\x2e\xe0\x02\x13\x01\x09'
    REAR_WINDOW_HEAT_ON = b'\x2e\xe0\x02\x14\x01\x08'

    L_TEMP_INC = b'\x2e\xe0\x02\x03\x01\x19'
    L_TEMP_DEC = b'\x2e\xe0\x02\x02\x01\x1a'
    R_TEMP_INC = b'\x2e\xe0\x02\x05\x01\x17'
    R_TEMP_DEC = b'\x2e\xe0\x02\x04\x01\x18'

    STUB_REQUEST = b'\x2e\x89\x03\x04\x37\x00\x38'  # stub request from HU -> Box

    ACK = b'\xff'

# HU - > VIM_AIR_CONDITIONING_PROPERTY
class AC_STATUS:
    ON = 1
    OFF = 0


# HU - > VIM_AIR_CONDITIONING_COOL_MODE_PROPERTY
class AC_COOL_MODE:
    ON = 1
    OFF = 0


# HU - > VIM_AIR_CONDITIONING_COOL_MODE_PROPERTY
class AC_COOL_MODE_AUTO:
    ON = 1
    OFF = 0


# HU - > VIM_AIR_CONDITIONING_COOL_MODE_PROPERTY
class AC_DUAL_MODE:
    ON = 1
    OFF = 0


# HU -> VIM_AIR_CONDITIONING_CYCLE_MODE_PROPERTY
class AC_CYCLE_MODE:
    INTERIOR = 1
    EXTERIOR = 0


class AC_WINDOW_MAX:
    ON = 1
    OFF = 0


# HU -> VIM_DEFROST_REAR_WINDOW_PROPERTY
class AC_REAR_WINDOW_HEAT:
    ON = 1
    OFF = 0


# HU -> VIM_HVAC_FAN_TARGET_TEMP_PROPERTY
class AC_TEMP:
    AC_TEMP_LO = 0x00
    AC_TEMP_HI = 0x1e
    F_16_0 = 0x1d
    F_16_5 = 0x1f
    F_15_0 = 0x20
    F_15_5 = 0x21
    F_31_0 = 0x22


# Fan Speed HU -> VIM_HVAC_FAN_SPEED_PROPERTY
# Seat Heat HU -> VIM_HEATER_DRVNG_SEAT_PROPERTY, VIM_HEATER_PSNGR_SEAT_PROPERTY
# Ext temp HU -> VIM_EXTERIOR_TEMP_PROPERTY

# HU - > VIM_HVAC_FAN_DIRECTION_PROPERTY
# HVAC_FAN_DIRECTION_UP_ON, HVAC_FAN_DIRECTION_CENTER_OFF, HVAC_FAN_DIRECTION_DOWN_OFF = [1, 0, 0]
class AC_FAN_DIR:
    AC_FAN_DIR_AUTO = 1  # [0, 0, 0]
    AC_FAN_DIR_FRONT_WINDOW = 2  # [1, 0, 0]
    AC_FAN_DIR_DOWN = 3  # [0, 0, 1]
    AC_FAN_DIR_DOWN_AND_CENTER = 4  # [0, 1, 1]
    AC_FAN_DIR_CENTER = 5  # [0, 1, 0]
    AC_FAN_DIR_CENTER_AND_UP = 6  # [1, 1, 0]
    AC_FAN_DIR_UP = 7  # [1, 0, 0]
    AC_FAN_DIR_UP_AND_DOWN = 8  # [1, , 1]
    AC_FAN_DIR_UP_DOWN_CENTER = 9  # [1, 1, 1]
    # HU Default = [0, 0, 0]


class FAN_DIR_SERVO_POSITION:
    LEFT = 0
    MIDDLE = 1
    RIGHT = 2


class RELAY_STATUS:
    ON = 0
    OFF = 1


class DOOR_STATUS:
    OPEN = 1
    CLOSE = 0


class DOOR_HEX_VALUE:
    TRUNK = 0x08
    RL = 0x10
    RR = 0x20
    FL = 0x40
    FR = 0x80
