import sys
from time import sleep

from machine import UART, Pin
from MCP2515 import MCP2515 as CAN
from canio import Match, Message

#47619
#500000
serial = sys.stdout
can = CAN(1, 10000000, 10, 11, 12, 13, baudrate=47619, debug=False)
led = Pin(25, Pin.OUT)

ECUReply = False
res = False


def asend_init_ECU():
    data = bytes([0x3f, 0x81, 0x01, 0x33, 0x02, 0x40, 0x00, 0x00])
    msg1 = Message(id=0x220, data=data)
    send_success = can.send(msg1)
    print('0x220 was sent')


def send_RPM():
    data = bytes([0x00, 0x10, 0x10, 0x00, 0x00, 0x00, 0x00, 0x00])
    msg1 = Message(id=0x1a0, data=data)
    send_success = can.send(msg1)

def send_msg(msg_id, msg_data):
    data = bytes(msg_data)
    msg1 = Message(id=msg_id, data=data)
    send_success = can.send(msg1)

def send_ECU_next_msg(msg):
    if msg.id == int(0x238):
        print('msg_id == int(0x238)', msg.id == int(0x238))
        # CMD = 0x1a
        CMD = 0x01
        # DATA = 0x0b  # MAP pressure
        DATA = 0x0c  # RPM
        msg2 = Message(id=0x240, data=bytes([0x40, 0xa1, 0x02, CMD, DATA, 0x00, 0x00, 0x00]))
        send_success = can.send(msg2)
    elif msg.id == int(0x258):
        print('msg_id == int(0x258)', msg.id == int(0x258))
        print('data', msg.data)
        print('data', msg.data[0])
        if msg.data[0] == int(0xc1):
            ROW = 0x81
        elif msg.data[0] == int(0xc2):
            ROW = 0x82
        elif msg.data[0] == int(0xc3):
            ROW = 0x83
        else:
            ROW = msg.data[0]

        msg2 = Message(id=0x266, data=bytes([0x40, 0xa1, 0x3f, ROW, 0x00, 0x00, 0x00, 0x00]))
        send_success = can.send(msg2)


IDS_TO_FILTER = []
# IDS_TO_FILTER = [int(0x238), int(0x258)]


listener = can.listen(timeout=1.0, matches=[Match(x) for x in IDS_TO_FILTER])


def hack(id_start, id_finish, repeat):
    for _id in range(int(id_start), int(id_finish)):
        data = [0x00] * 8
        for idx in range(len(data)):
            for i in range(int(0x00), int(0xff)):
                data[idx] = i
        can.send(Message(id=_id, data=bytes(data)))


def start_listen():
        message_count = listener.in_waiting()
        if message_count == 0:
            return
        for i in range(message_count):
            msg = listener.receive()
            led.value(1)
            unpacked_data = [int(hex(x), 16) for x in msg.data]
            send_ECU_next_msg(msg)
            print("ID: {}, data: {}".format(hex(msg.id), unpacked_data))
            sys.stdout.write(bytes([0x44, 0x33, 0x22, 0x11]))
            sys.stdout.write(msg.id.to_bytes(4, 'little'))
            sys.stdout.write(bytes(unpacked_data))
            led.value(0)

            # msg = can.recv_msg()
            # if msg:
            #     led.value(1)
            #     print([0x668, 0x77, 0x11, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88])
            #     print(msg.get('data'))
            #     unpacked_data = [int(hex(x), 16) for x in msg.get('data')]
            #     print('unpacked_data', unpacked_data)
            #     id = int(msg.get('id'))
            #     print("ID: {}, data: {}".format(hex(msg.get('id')), unpacked_data))
            #     sys.stdout.write(bytes([0x44, 0x33, 0x22, 0x11]))
            #     sys.stdout.write(id.to_bytes(4, 'little'))
            #     sys.stdout.write(bytes(unpacked_data))
            #     led.value(0)


def handle_can_cmd(_):
    start_listen()


can_interrupt_pin = Pin(0, Pin.IN, Pin.PULL_UP)
can_interrupt_pin.irq(trigger=Pin.IRQ_FALLING, handler=handle_can_cmd, )


def sendSerailFrame(msg):
    # print("send:", msg[0], msg[1:])
    frame_id = msg[0]
    print('frame_id', frame_id)
    serial.write(bytes([0x44, 0x33, 0x22, 0x11]))
    serial.write(frame_id.to_bytes(4, 'little'))

    # frame_data = [int(value, 16) for value in msg[1:]]
    frame_data = msg[1:]
    frame_data.extend([0] * (8 - len(frame_data)))
    print("frame_data:", frame_data)
    serial.write(bytes(frame_data))

# 0x640 [0x00, 0x00, 0x00, 0x00, 0xff, 0x00, 0x00, 0x00] CruiseOn
# 0x318 [0x00, 0x00, ABS, MILEAGE, 0xff, 0x00, 0x00, 0x00]
# ABS
# 0x10 - drift
# 0x20 - drift OFF
# 0x80 - ABS+BRAKE
# 0x10 | 0x20 | 0x80
# MILEAGE

# 0x880 [0, 0, TURBO1, TURBO2]
# TURBO2 Vacuum


def starthack():
    # START = 0x00
    START = 880
    # FINISH = 10000
    FINISH = 10000
    BIT_ID_START = 0
    BIT_ID_END = 8
    BIT_START = 0
    BIT_END = 255
    STEP = 16


    for _id in range(START, FINISH):
        for bit_id in range(BIT_ID_START, BIT_ID_END):
            for bit in range(BIT_START, BIT_END, STEP):
                data1 = [0xff, 0xff, 0x70, 0xff, 0xff, 0xff, 0xff, 0xff]
                data = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
                data[bit_id] = bit
                # send_RPM()
                send_msg(_id, data)
                sleep(0.001)
                print(_id, bit_id, bit)

def startFFF():
    START = 20000
    # FINISH = 10000
    FINISH = 100000
    for _id in range(START, FINISH):
        data1 = [0xff, 0xff, 0x70, 0xff, 0xff, 0xff, 0xff, 0xff]
        data0 = [0x10, 0x20, 0x30, 0x40, 0x50, 0x60, 0x70, 0x80]
        send_msg(_id, data1)
        sleep(0.001)
        print(_id)

# startFFF()

# starthack()

def start():
    pass

start_listen()