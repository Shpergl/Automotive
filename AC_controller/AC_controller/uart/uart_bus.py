from machine import UART, Pin

from AC_controller.constants import UART_COMMANDS
from AC_controller.controllers.climate_controller import get_climate_controller
from AC_controller.controllers.door_controller import get_door_controller
from AC_controller.controllers.parking_controller import (get_front_parking_controller,
                                                                  get_rear_parking_controller)
from AC_controller.helpers.observer import Observer
from AC_controller import settings
from AC_controller.uart.uart_commands import UARTCmdHandlers


class UARTBus(Observer):
    def __init__(self):
        self._uart = UART(settings.UART.ID, baudrate=settings.UART.BAUDRATE,
                          tx=Pin(settings.UART.TX_PIN),
                          rx=Pin(settings.UART.RX_PIN),
                          bits=8, stop=1)

        # subscribe to controller updates
        self.subscribe(get_climate_controller())
        self.subscribe(get_door_controller())
        self.subscribe(get_front_parking_controller())
        self.subscribe(get_rear_parking_controller())

    def _build_packet(self, type, buf, size):
        buf.insert(0, settings.UART.HEADER)
        buf.insert(1, type)
        buf.insert(2, size)
        buf.append(sum(buf[1:]) ^ settings.UART.CHECKSUM_XOR)
        return buf

    def update(self, subject_type, subject):
        data = subject.get_packed_data()
        self._send(subject.controller_type, data)

    def _send(self, data_type, data):
        """ Send UART commands to HU """
        packet = self._build_packet(data_type, data, len(data))
        print('[UARTBus] Sending paket: {}'.format(data))
        import time
        time.sleep(settings.UART.RESPONSE_TIMEOUT)
        self._uart.write(bytearray(packet))

    def handle_uart_cmd(self, _):
        """ Handle UART commands from HU """
        raw_data = self._uart.read()
        cmd = UARTCmdHandlers.get(raw_data)
        if cmd:
            self._uart.write(UART_COMMANDS.ACK)
            cmd()


UART_bus = None


def get_UART_bus():
    global UART_bus
    if UART_bus is None:
        UART_bus = UARTBus()

    return UART_bus
