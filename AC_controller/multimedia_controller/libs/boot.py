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


class ADCDevice:
    def __init__(self, i2c_bus, address=72):
        self._i2c = i2c_bus
        self._address = address

    def read_config(self):
        self._i2c.writeto(self._address, bytearray([1]))
        result = self._i2c.readfrom(self._address, 2)
        return result[0] << 8 | result[1]

    def read_value(self):
        self._i2c.writeto(self._address, bytearray([0]))
        result = self._i2c.readfrom(self._address, 2)
        config = self.read_config()
        config &= ~(7 << 12) & ~(7 << 9)
        config |= (4 << 12) | (1 << 9) | (1 << 15)
        config = [int(config >> i & 0xff) for i in (8, 0)]
        self._i2c.writeto(self._address, bytearray([1] + config))
        return result[0] << 8 | result [1]

    @staticmethod
    def val_to_voltage(val, max_val=26100, voltage_ref=5.0):
        return val/max_val * voltage_ref

from machine import I2C, Pin
i2c_bus = I2C(1, scl=Pin(31), sda=Pin(32))
devices = i2c_bus.scan()
for device in devices:
    print(device)

adc = ADCDevice(i2c_bus)
print(bin(adc.read_config()))

def measureVoltage():
    val = adc.read_value()
    voltage = adc.val_to_voltage(val)
    print("ADC Value: {}, voltage: {:.3f} V".format(val, voltage))




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


def start_listen():
    while True:
        msg = can.recv_msg()
        if msg:
            unpacked_data = [hex(x) for x in bytearray(msg.get('data'))]
            id = hex(msg.get('id'))
            if id not in msgs:
                msgs[id] = [unpacked_data]
            else:
                msgs[id].append(unpacked_data)

            #if (msg.get('id')) == int(0x460):
            #    rpm = int(unpacked_data[1])*256 + int(unpacked_data[2])
                #print("RPM: {}".format(rpm))

            print("ID: {}, data: {}".format(hex(msg.get('id')), unpacked_data))


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
