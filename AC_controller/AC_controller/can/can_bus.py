from machine import Timer

from AC_controller.libs import mcpcan
from AC_controller.settings import CAN

from AC_controller.helpers.observer import Observer
from AC_controller.can.can_commands import CANCmdHandlers


class CanBus(Observer):
    def __init__(self):
        self._can = mcpcan.CAN(CAN.ID, CAN.SPI_BAUDRATE,
                               CAN.SPI_SCK_PIN, CAN.SPI_MOSI_PIN,
                               CAN.SPI_MISO_PIN, CAN.SPI_CS_PIN)

        self._can.start(speed_cfg=CAN.BITRATE)
        # TODO implement interrupt signal on MCP2515 chip instead of Timer Callback
        #self._timer = Timer(period=1, mode=Timer.PERIODIC, callback=self.handle_can_cmd)
        # subscribe to controller updates
        # self.subscribe(get_climate_controller())
        # self.subscribe(get_door_controller())

    def _build_packet(self, cmd_id, buf, size, remote=False):
        packet = dict()
        packet['id'] = int(cmd_id)
        packet['dlc'] = size
        packet['data'] = bytearray(buf)
        packet['rtr'] = remote
        packet['ext'] = False
        return packet

    def update(self, subject_type, subject):
        data = subject.get_packed_data()
        self.send(subject.controller_type, data)

    def send(self, data_type, data):
        """ Send CAN command to devices """
        packet = self._build_packet(data_type, data, len(data))
        print('[UARTBus] Sending paket: {}'.format(data))
        self._can.send_msg(packet)

    def handle_can_cmd(self, _):
        """ Handle CAN commands from car devices """
        msg = self._can.recv_msg()
        if msg:
            can_id = msg.get('id')
            cmd = CANCmdHandlers.get(can_id)
            if cmd:
                cmd(msg)


CAN_bus = None


def get_CAN_bus():
    global CAN_bus
    if CAN_bus is None:
        CAN_bus = CanBus()

    return CAN_bus
