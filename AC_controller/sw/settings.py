from constants import AC_TEMP, FAN_DIR_SERVO_POSITION

DUBUG_MODE = 1  # 0 (off), 1 (on)

UART_COMMAND_DEBOUNCE_TIMEOUT = 100
CAN_COMMAND_DEBOUNCE_TIMEOUT = 10


class PINS:
    UART_TX_PIN = 0
    UART_RX_PIN = 1
    ONE_WIRE_TEMP_SENSORS_PIN = 2
    SEAT_HEAT_L = 3
    SEAT_HEAT_R = 4
    POWER_SUPPLY_PIN = 5
    VCC_RELAY_PIN = 6

    SUN_SENSOR_PIN = 7  #TODO

    CAN_INTERRUPT_PIN = 9
    CAN_SPI_SCK_PIN = 10
    CAN_SPI_MOSI_PIN = 11  # RP -> TX
    CAN_SPI_MISO_PIN = 12  # RP -> RX
    CAN_SPI_CS_PIN = 13

    AC_COMPRESSOR_RELAY = 16
    AC_REAR_WINDOW_HEAT_RELAY = 17
    AC_COOLANT_RELAY = 18
    AC_CYCLE_RELAY = 19
    AC_FAN = 8  # 20 fix. Default is 20
    AC_TEMP_SERVO = 21
    FAN_DIR_DOWN_MIDDLE_SERVO = 22
    ADC_SDA = 26
    ADC_SCL = 27
    FAN_DIR_WINDOW_SERVO = 28
    # AC_COMPRESSOR_FAN_RELAY = 19


class TEMP_SENSORS:
    INT = 1
    INT_L = 2
    INT_R = 3
    COOLER = 4
    MIXED = 5


# Sensors address could be found from ds18x20.DS18X20(onewire.OneWire(Pin(self._pin))).scan()
ONE_WIRE_TEMP_SENSORS = {
    TEMP_SENSORS.INT: bytes([0x28, 0x2b, 0x38, 0x59, 0x94, 0x21, 0x06, 0xcf]),  # b'\x28\x2b\x38\x59\x94\x21\x06\xcf'
    TEMP_SENSORS.INT_L: bytes([0x28, 0xce, 0x21, 0x50, 0x95, 0x21, 0x06, 0xba]),  # b'\x28\xce\x21\x50\x95\x21\x06\xba'
    # TEMP_SENSORS.INT_R: bytes([0x28, 0x86, 0xe6, 0x66, 0x94, 0x21, 0x06, 0xf7]),  # b'\x28\x86\xe6\x66\x94\x21\x06\xf7'
    TEMP_SENSORS.MIXED: bytes([0x28, 0x02, 0xbc, 0x50, 0x94, 0x21, 0x06, 0xa8]),  # b'\x28\x02\xbc\x50\x94\x21\x06\xa8'
    TEMP_SENSORS.COOLER: bytes([0x28, 0xa4, 0x63, 0x57, 0x94, 0x21, 0x06, 0xf1])  # b'\x28\xa4\x63\x57\x94\x21\x06\xf1'
}
ONE_WIRE_TEMP_SENSORS_ID_TO_NAME = {v: k for k, v in ONE_WIRE_TEMP_SENSORS.items()}

ONE_WIRE_MEASURE_TIME = 750
ONE_WIRE_MEASURE_PERIOD = 1000  # ms
CAN_STATUS_MESSAGE_SEND_PERIOD = 1000  # ms
SHUTTING_DOWN_TIMEOUT = 2000
ADC_MEASURING_PERIOD = 5000
AC_AUTO_MODE_PERIOD = 30000  # 30 sec

EXT_TEMP_RANGE = [x for x in range(-39, 80)]  # [-39, ... 79]

AC_LOWEST_TEMP = 16.5
AC_HIGHEST_TEMP = 31

AC_TEMP_DEVIATION = 2  # TODO
ACC_VOLTAGE_THRESHOLD = 10  # volts

SERVO_PWM_FREQ = 50
FAN_DIR_SERVO_POSITIONS = [FAN_DIR_SERVO_POSITION.LEFT, FAN_DIR_SERVO_POSITION.MIDDLE, FAN_DIR_SERVO_POSITION.RIGHT]
FAN_DIR_WINDOW_DUTIES = {FAN_DIR_SERVO_POSITION.LEFT: 1600,
                         FAN_DIR_SERVO_POSITION.MIDDLE:  4320,
                         FAN_DIR_SERVO_POSITION.RIGHT: 7040}

FAN_DIR_DOWN_MIDDLE_DUTIES = {FAN_DIR_SERVO_POSITION.LEFT: 1600,
                              FAN_DIR_SERVO_POSITION.MIDDLE:  4320,
                              FAN_DIR_SERVO_POSITION.RIGHT: 7040}

AC_TEMP_RANGE = [x for x in range(0, 29)] + [AC_TEMP.AC_TEMP_HI]  # will be converted to [LO, 17.0, 17.5, ... 30.5, HI]
#res = max(AC_LOWEST_TEMP, min(AC_HIGHEST_TEMP, AC_LOWEST_TEMP + (temp-1) * 0.5))
AC_TEMP_DUTIES_RANGE = [1600, 7040]

FAN_PWM_FREQ = 50
FAN_SPEED_RANGE = [0, 1, 2, 3, 4, 5, 6, 7]
FAN_SPEED_DUTIES_RANGE = [0, 15000, 20000, 25000, 30000, 35000, 40000, 50000]  # [0, 1, 2, 3, 4, 5, 6, 7]

SEAT_HEAT_PWM_FREQ = 50
SEAT_HEAT_RANGE = [0, 1, 2, 3]
SEAT_HEAT_DUTIES_RANGE = [0, 100000]


# 0 - 1023 ESP32
# servo * 64 -> 110 * 64 = servo.duty_u16(7040)


class UART:
    ID = 0
    BAUDRATE = 38400
    RESPONSE_TIMEOUT = 0.2


class CAN:
    ID = 1
    SPI_BAUDRATE = 10000000
    BAUDRATE = 47619  # bps
    IDS_TO_FILTER = []  # [int(0x368)]
    # 47619 bps I-bus, 500000 bps P-bus


class I2C:
    ID = 1


class F_PARKING_RANGE:
    L = [1, 2, 4, 6, 8]
    LC = [1, 2, 4, 6, 8, 9]
    RC = [1, 2, 4, 6, 8, 9]
    R = [1, 2, 4, 6, 8]


class R_PARKING_RANGE:
    L = [1, 2, 4, 6, 8]
    LC = [1, 2, 4, 6, 8, 9]
    RC = [1, 2, 4, 6, 8, 9]
    R = [1, 2, 4, 6, 8]


PARKING_SENSOR_VALUES_RANGE = [0, 255]
