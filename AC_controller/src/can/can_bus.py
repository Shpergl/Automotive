from libs.MCP2515 import MCP2515
from libs.canio import Message, Match
from settings import CAN, PINS, DUBUG_MODE

from helpers.observer import Observer
from can.can_commands import CANCmdHandlers

from controllers.climate_controller import get_climate_controller


class CanBus(Observer):
    LISTEN_TIMEOUT = 1.0

    def __init__(self):
        self._can = MCP2515(CAN.ID, CAN.SPI_BAUDRATE,
                            PINS.CAN_SPI_SCK_PIN, PINS.CAN_SPI_MOSI_PIN,
                            PINS.CAN_SPI_MISO_PIN, PINS.CAN_SPI_CS_PIN,
                            baudrate=CAN.BAUDRATE)
        self._listener = self._can.listen(timeout=self.LISTEN_TIMEOUT, matches=[Match(x) for x in CAN.IDS_TO_FILTER])
        # subscribe to controller updates
        self.subscribe(get_climate_controller())

    def _build_message(self, cmd_id, buf):
        return Message(id=cmd_id, data=bytearray(buf))

    def send(self, data_id, data):
        """ Send CAN command to devices """
        message = self._build_message(data_id, data)
        send_success = self._can.send(message)
        if DUBUG_MODE:
            print('[CANBus] Message {}/{} send status: {}'.format(hex(data_id), data, send_success))

    def handle_can_cmd(self, _):
        """ Handle CAN commands from car devices """
        message_count = self._listener.in_waiting()
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
