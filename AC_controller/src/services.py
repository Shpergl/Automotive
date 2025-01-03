from machine import Pin, Timer

import settings
from can.can_commands import ACCTempCommand
from constants import RELAY_STATUS
from devices.relays import BaseRelay

from can.can_bus import get_CAN_bus


class CanStatusReporterService:
    def __init__(self,):
        self._periodic_commands = [ACCTempCommand()]
        self._can_bus = get_CAN_bus()
        self._timer = Timer()
        self._timer.init(mode=Timer.PERIODIC,
                         callback=self._on_timer,
                         period=settings.CAN_STATUS_MESSAGE_SEND_PERIOD)

    def _on_timer(self, _):
        for command in self._periodic_commands:
            # command = CANCmdHandlers.get(command_name)
            self._can_bus.send(*command.build())


class ShutDownService:
    def __init__(self):
        self._vcc_relay = BaseRelay('VccRelay', settings.PINS.VCC_RELAY_PIN)
        self._timer = Timer()
        self._is_shutting_down = False
        self._power_supply_pin = Pin(settings.PINS.POWER_SUPPLY_PIN, Pin.IN, Pin.PULL_UP)
        self._power_supply_pin.irq(trigger=Pin.IRQ_RISING, handler=self._handle_power_interrupt)

    def shutdown(self, _):
        self._is_shutting_down = False
        self._timer.deinit()
        self._vcc_relay.state = RELAY_STATUS.OFF

    def _handle_power_interrupt(self, pin):
        if pin.value() == 1 and not self._is_shutting_down:
            self._is_shutting_down = True
            self._vcc_relay.state = RELAY_STATUS.ON
            self._timer.init(period=settings.SHUTTING_DOWN_TIMEOUT, mode=Timer.ONE_SHOT, callback=self.shutdown)
            # with open('/state.txt', 'w') as f:
            #    f.write('ON')


# class AccVoltage
