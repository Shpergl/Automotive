# TODO debug file. remove it

import time

from mcpcan import CAN

can = CAN(1, 10000000, 10, 11, 12, 13)


read = 0

speed = 1
max_speed = 81

def send(_id, data):
    packet = {}
    packet['id'] = int(_id)
    packet['dlc'] = len(data)
    packet['data'] = bytearray(data)
    packet['rtr'] = False
    packet['ext'] = False
    can.send_msg(packet)
can.start(speed_cfg=47619)


from machine import I2C, Pin, PWM
from ads1x15 import ADS1115
i2c_bus = I2C(1, scl=Pin(27), sda=Pin(26))
devices = i2c_bus.scan()
adc = ADS1115(i2c_bus, address=72, gain=0)


fan = PWM(Pin(16))
fan.freq(20000)


def speed(value):
    global fan
    fan.duty_u16(value)


import onewire, ds18x20

class TEMP_SENSORS:
    COOLER = 4
    MIXED = 5

ONE_WIRE_TEMP_SENSORS = {
    TEMP_SENSORS.MIXED: b'\x28\x02\xbc\x50\x94\x21\x06\xa8',
    TEMP_SENSORS.COOLER: b'\x28\xa4\x63\x57\x94\x21\x06\xf1',
}

ow = onewire.OneWire(Pin(15))
ds = ds18x20.DS18X20(ow)


def round_float(value):
    return round(value*2)/2


def measure():
    ds.convert_temp()
    for sensor_name, sensor_id in ONE_WIRE_TEMP_SENSORS.items():
        print("{}: {}".format(sensor_name, round_float(ds.read_temp(sensor_id))))


def handle_timer(_):
    print("\n")
    measure()
    measure_voltage()

#from machine import Timer
#timer = Timer(period=10000, mode=Timer.PERIODIC, callback=handle_timer)

from machine import time_pulse_us
import time

PULSE_LEVEL = 1
START_BIT_TIMEOUT = 1200
START_BIT_LOW_BOUND = 900
START_BIT_HIGH_BOUND = 1100

HIGH_BIT_LOW_BOUND = 230
HIGH_BIT_HIGH_BOUND = 260

HIGH_BIT_TIMEOUT = 300

SENSOR_ADDR_MAP = {
    0: 'Rear Left A',  # 5 A 0b10000000
    1: 'Rear Left Center B',  # 6 B 0b10000001
    2: 'Rear Right Center C',  # 7 C 0b10000010
    3: 'Rear Right D',  # 8 D 0b10000011
    4: 'Front Left E',  # 1, E 0b10010100
    5: 'Front Left Center F',  # 2 F 0b10010101
    6: 'Front Right Center G',  # 3 G 0b10010110
    7: 'Front Right H',  # 4 H 0b10010111
}


def get_packet(pin):
    start_pulse_duration = time_pulse_us(pin, PULSE_LEVEL, START_BIT_TIMEOUT)
    if START_BIT_LOW_BOUND < start_pulse_duration < START_BIT_HIGH_BOUND:
        packet = 0
        for i in range(15, -1, -1):
            bit_pulse_duration = time_pulse_us(pin, PULSE_LEVEL, HIGH_BIT_TIMEOUT)
            if HIGH_BIT_LOW_BOUND < bit_pulse_duration < HIGH_BIT_HIGH_BOUND:
                packet |= 1 << i
        addr = (packet >> 8) & 0b00001111
        value = packet & 0b11111111
        #print("Addr: {}, {}".format(SENSOR_ADDR_MAP.get(addr), value))
        return addr, value


radars = {}
def start_listening_puls():
    while True:
        pin = Pin(16, Pin.IN, Pin.PULL_DOWN)
        addr, value = get_packet(pin)
        radars[addr] = value


def measure_voltage():
    value1 = adc.read(0, 0)
    value2 = adc.read(0, 1)
    # print(value1)
    # print(value2)
    v1 = adc.raw_to_v(value1)
    v2 = adc.raw_to_v(value2)
    print("Voltage1: {}".format(v2))
    print("Voltage2: {}".format(v1*3))


def handle_can_cmd(_):
    # ceck = can.check_rx()
    # print('check {}'.format(ceck))
    print('handle')


    #for i in range(10):
    #can._spi_RecvMsg(0)
    can.check_rx()
    for msg in can._rx_buf:
        print('msg')
    can.recv_msg()
    #can.get_msg()


            # unpacked_data = [hex(x) for x in bytearray(msg.get('data'))]
            # id = hex(msg.get('id'))
            #print('ID: {}, data: {}'.format(id, unpacked_data))

#from machine import Pin

#can_interrupt_pin = Pin(16, Pin.IN)
#can_interrupt_pin.irq(trigger=Pin.IRQ_FALLING, handler=handle_can_cmd)

msgs = {}

def startACC():
    send(0x530, [0x01, 0x04, 0x00, 0x14, 0x00, 0x00, 0x00, 0x00])   # AC on P 20 bar
    send(0x520, [0x01, 0x80, 0x00, 0x14, 0x00, 0x00, 0x00, 0x00])

def start_listen():
    while True:
        msg = can.recv_msg()
        if msg:
            unpacked_data = [hex(x) for x in msg.get('data')]
            id = hex(msg.get('id'))
            #print("ID: {}, data: {}".format(id, unpacked_data))
            m = msgs.get(id)
            if m and m != unpacked_data:
                if id == '0x6a8':
                    continue
                print("ID: {}, data: {}".format(hex(msg.get('id')), unpacked_data))
            else:
                msgs[id] = unpacked_data

            #if (msg.get('id')) == int(0x460):
            #    rpm = int(unpacked_data[1])*256 + int(unpacked_data[2])
                #print("RPM: {}".format(rpm))

start_listen()

def temp():
    _id = 0x7a0
    data = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
    data[1] = 0x01
    data[2] = 0x72
    data[3] = 0x01
    data[4] = 0x6d
    send(_id, data)

def text_c():
    #_id = 0x348 # AUDIO_TEXT_CNTRL
    _id = 0x34c  # ACC_TEXT_CNTRL
    data = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
    #data[0] = 0x11  # 0x011 AUDIO
    data[0] = 0x18  # 0x018 ACC
    data[1] = 0x00  # 0x00 -1,2 rows,0x01 - 2 row, 0x02 - ?
    data[2] = 0x00  # Priority - 0x00 -higher 0xff - lower
    data[3] = 0x23  # Priority - 0x00 -higher 0xff - lower
    send(_id, data)

def text():
#    _id = 0x328  # 0x328 SID_AUDIO_TEXT
    _id = 0x328  # 0x328 ACC
    data = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
    data[0] = 0x42  # Order 0x42 -> 0x01 -> 0x00
    data[1] = 0x96
    data[2] = 0x01  # Row 0x01 - 1, 0x02 - 2
    data[3] = 0x75  # text4
    data[4] = 0x31  # text3
    data[5] = 0x20  # text2
    data[6] = 0x4b  # text1
    data[7] = 0x49  # text0
    send(_id, data)
    time.sleep(0.01)
    data[0] = 0x01
    data[3] = 0x53
    data[4] = 0x53
    data[5] = 0x20
    data[6] = 0x46
    data[7] = 0x4d
    send(_id, data)
    time.sleep(0.01)
    data[0] = 0x00
    data[3] = 0x20
    data[4] = 0x01
    data[5] = 0x00
    data[6] = 0x00
    data[7] = 0x00
    send(_id, data)

def chunkstring(string, length):
    return [string[0+i:length+i] for i in range(0, len(string), length)]

def ascii_to_hex(char):
    return int('0x{:x}'.format(ord(char)), 16)


def show_text(text):
    _id = 0x32c  # 0x328 ACC
    acc_text_order = (0x45, 0x04, 0x03, 0x02, 0x01, 0x00)
    max_raw_len = 12
    raw_string = chunkstring(text, max_raw_len)
    print(raw_string)

    for msg_idx, msg_ord in enumerate(acc_text_order):
        data = [0x00, 0x96, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
        data[0] = msg_ord  # Order 0x42 -> 0x01 -> 0x00
         #if msg_idx <= 2 else 0x81  # Row 0x01 - 1, 0x02 - 2
        if msg_idx < 3:
            data[2] = 0x81
            chunk_string = chunkstring(raw_string[0], 5)
            chunk_idx = msg_idx
        else:
            data[2] = 0x82
            chunk_string = chunkstring(raw_string[1], 5) if len(raw_string) > 2 else []
            chunk_idx = msg_idx - 3

        if chunk_idx < len(chunk_string):
            for i, c in enumerate(chunk_string[chunk_idx]):
                data[3 + i] = ascii_to_hex(c)

        send(_id, data)
        msg_idx += 1
        time.sleep(0.01)


data = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
data[0] = 0x00
data[1] = 0x00
data[2] = 0x00
data[3] = 0x00
data[4] = 0x01
data[5] = 0x06
data[6] = 0x10
data[7] = 0x08



def s():
    for i in range(0, 12):
        data = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
        data[0] = 0x00
        data[1] = 0x00
        data[2] = 0x00
        data[3] = 0x00
        data[4] |= i << 4
        data[4] |= i << 0
        data[5] |= i << 4
        data[5] |= i << 0
        data[6] |= i << 4
        data[6] |= i << 0
        data[7] |= i << 4
        data[7] |= i << 0
        send(0x439, data)
        time.sleep(1)

def t():
    d = [0x00, 0x01, 0x01, 0x01, 0x00, 0x02, 0x00, 0x00]
    #d = [0x00, 0x02, 0x80, 0x02, 0x00, 0x00, 0x00, 0x00]
    send(0x7a0, d)
    time.sleep(1)

for i in range(5):
    pass
    #t()
    #s()
