INPUT_PULSE_PIN = 16
FRONT_RADAR_PIN = 6
REAR_RADAR_PIN = 7

PULSE_LEVEL = 1
START_BIT_TIMEOUT = 1200
START_BIT_LOW_BOUND = 900
START_BIT_HIGH_BOUND = 1100

HIGH_BIT_TIMEOUT = 300
HIGH_BIT_LOW_BOUND = 230
HIGH_BIT_HIGH_BOUND = 260

SENSOR_ADDR_NAME_MAP = {
    0: 'Rear Left A',  # 5 A 0b10000000
    1: 'Rear Left Center B',  # 6 B 0b10000001
    2: 'Rear Right Center C',  # 7 C 0b10000010
    3: 'Rear Right D',  # 8 D 0b10000011
    4: 'Front Left E',  # 1, E 0b10010100
    5: 'Front Left Center F',  # 2 F 0b10010101
    6: 'Front Right Center G',  # 3 G 0b10010110
    7: 'Front Right H',  # 4 H 0b10010111
}