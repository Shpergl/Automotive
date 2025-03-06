import uasyncio

from libs.MCP2515 import MCP2515
from libs.canio import Message, Match
from settings import CAN, PINS, DUBUG_MODE

from helpers.observer import Observer
from commands import CANCmdHandlers

from controllers.climate_controller import get_climate_controller


class CanBus(Observer):
    LISTEN_TIMEOUT = 0.5

    def __init__(self):
        self._can = MCP2515(CAN.ID, CAN.SPI_BAUDRATE,
                            PINS.CAN_SPI_SCK_PIN, PINS.CAN_SPI_MOSI_PIN,
                            PINS.CAN_SPI_MISO_PIN, PINS.CAN_SPI_CS_PIN,
                            baudrate=CAN.BAUDRATE)
        self._listener = self._can.listen(timeout=self.LISTEN_TIMEOUT, matches=[Match(x) for x in CAN.IDS_TO_FILTER])
        # subscribe to controller updates
        self._send_message_queue = []
        self.subscribe(get_climate_controller())

    def add_loop_tasks(self, loop):
        loop.create_task(self.send_task())
        loop.create_task(self.receive_task())

    def send(self, data_id, data):
        message = Message(id=data_id, data=bytearray(data))
        self._send_message_queue.append(message)

    async def send_task(self):
        """ Send CAN command to devices """
        while True:
            if len(self._send_message_queue) == 0:
                await uasyncio.sleep_ms(0)
                continue
            msg = self._send_message_queue.pop(0)
            send_success = self._can.send(msg)
            if DUBUG_MODE:
                print('[CANBus] Message {}/{} send status: {}'.format(hex(msg.id), msg.data, send_success))

    async def receive_task(self):
        """ Handle CAN commands from car devices """
        while True:
            message_count = self._listener.in_waiting()
            if message_count == 0:
                await uasyncio.sleep_ms(0)
                continue
            for i in range(message_count):
                msg = self._listener.receive()
                if msg:
                    if DUBUG_MODE:
                        print('[CANBus] Message {}/{} received'.format(msg.id, msg.data))
                    cmd = CANCmdHandlers.get(msg.id)
                    if cmd:
                        cmd(msg)


CAN_bus = None


def get_CAN_bus():
    global CAN_bus
    if CAN_bus is None:
        CAN_bus = CanBus()

    return CAN_bus
