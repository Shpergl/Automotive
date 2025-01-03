from machine import Pin, Timer

import settings
from helpers.observer import Observer
from constants import UART_TYPES, AC_COOL_MODE, AC_STATUS, AC_CYCLE_MODE, AC_REAR_WINDOW_HEAT, RELAY_STATUS
from controllers.climate_controller import get_climate_controller


"""
Init all devices in boot.py -> init_devices()
"""


class BaseRelay:
    def __init__(self, name, pin):
        self._name = name
        self._pin = pin
        self._relay = None
        self._current_state = None
        self.init()
        self.state = RELAY_STATUS.OFF

    def init(self):
        self._relay = Pin(self._pin, Pin.OUT)

    @property
    def state(self):
        return self._current_state

    @state.setter
    def state(self, state):
        if self._current_state != state:
            self._current_state = state
            self._relay.value(state)
            if settings.DUBUG_MODE:
                print('{} changed state to: {}'.format(self._name, self.state))


class ACCompressorRelay(Observer):
    def __init__(self):
        self._relay = BaseRelay('ACCompressorRelay', settings.PINS.AC_COMPRESSOR_RELAY)
        self.subscribe(get_climate_controller())

    def update(self, subject_type, subject):
        if subject_type == UART_TYPES.AC:
            self._relay.state = RELAY_STATUS.ON if subject.ac == AC_COOL_MODE.ON else RELAY_STATUS.OFF


class ACCompressorFanRelay(Observer):
    def __init__(self):
        self._relay = BaseRelay('ACCompressorFanRelay', settings.PINS.AC_COMPRESSOR_FAN_RELAY)
        self.subscribe(get_climate_controller())

    def update(self, subject_type, subject):
        if subject_type == UART_TYPES.AC:
            if subject.ac == AC_COOL_MODE.ON:
                # TODO check AC pressure to on/off relay. AC_COOL_MODE is only directive to start AC process.
                self._relay.state = RELAY_STATUS.ON
            elif subject.ac == AC_COOL_MODE.OFF:
                self._relay.state = RELAY_STATUS.OFF


class ACCycleRelay(Observer):
    def __init__(self):
        self._relay = BaseRelay('ACCycleRelay', settings.PINS.AC_CYCLE_RELAY)
        self.subscribe(get_climate_controller())

    def update(self, subject_type, subject):
        if subject_type == UART_TYPES.AC:
            if subject.cycle == AC_CYCLE_MODE.INTERIOR:
                self._relay.state = RELAY_STATUS.ON
            elif subject.cycle == AC_CYCLE_MODE.EXTERIOR:
                self._relay.state = RELAY_STATUS.OFF


class ACCoolantRelay(Observer):
    """
    Turn on vacuum valve in engine bay to prevent coolant circulation in internal radiator
    """
    def __init__(self):
        self._relay = BaseRelay('ACCoolantRelay', settings.PINS.AC_COOLANT_RELAY)
        self.subscribe(get_climate_controller())

    def update(self, subject_type, subject):
        if subject_type == UART_TYPES.AC:
            self._relay.state = RELAY_STATUS.ON if subject.ac == AC_COOL_MODE.ON else RELAY_STATUS.OFF


class ACRearWindowHeatRelay(Observer):
    def __init__(self):
        self._relay = BaseRelay('ACRearWindowHeatRelay', settings.PINS.AC_REAR_WINDOW_HEAT_RELAY)
        self.subscribe(get_climate_controller())

    def update(self, subject_type, subject):
        if subject_type == UART_TYPES.AC:
            if subject.rear_window_heat == AC_REAR_WINDOW_HEAT.ON:
                self._relay.state = RELAY_STATUS.ON
            elif subject.rear_window_heat == AC_REAR_WINDOW_HEAT.OFF:
                self._relay.state = RELAY_STATUS.OFF
