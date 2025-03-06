from machine import Timer

import settings
# import commands
from constants import (
    UART_TYPES, AC_CYCLE_MODE, AC_STATUS, AC_COOL_MODE, AC_COOL_MODE_AUTO, AC_DUAL_MODE, AC_WINDOW_MAX,
    AC_FAN_DIR, AC_REAR_WINDOW_HEAT, CONTROLLER_TYPES, SUN_SENSOR_STATUS
)
from controllers.base_controller import BaseController, SequentialSelector, CycledSelector, BaseStateSelector

from settings import FAN_SPEED_RANGE, SEAT_HEAT_RANGE, AC_TEMP_RANGE, EXT_TEMP_RANGE


# from devices.sid_text import get_sid_text_device


class ClimateController(BaseController):
    DATA_FIELD_LENGTH = 7

    def __init__(self):
        super(ClimateController, self).__init__(UART_TYPES.AC)
        self.ac_status = AC_STATUS.OFF
        self.ac = AC_COOL_MODE.OFF
        self.auto = AC_COOL_MODE_AUTO.OFF
        self.dual = AC_DUAL_MODE.ON  # Dual is always on because of one climate zone in current car
        self.l_temp = SequentialSelector(AC_TEMP_RANGE, min(AC_TEMP_RANGE))
        self.r_temp = SequentialSelector(AC_TEMP_RANGE, min(AC_TEMP_RANGE))
        self._fan_speed = SequentialSelector(FAN_SPEED_RANGE, min(FAN_SPEED_RANGE))
        self.l_seat_heat = CycledSelector(SEAT_HEAT_RANGE, min(SEAT_HEAT_RANGE))
        self.r_seat_heat = CycledSelector(SEAT_HEAT_RANGE, min(SEAT_HEAT_RANGE))
        self.ext_temp = BaseStateSelector(EXT_TEMP_RANGE, 0)
        self.fan_dir = AC_FAN_DIR.AC_FAN_DIR_UP_DOWN_CENTER
        self.cycle = AC_CYCLE_MODE.EXTERIOR
        self._window_max = AC_WINDOW_MAX.OFF
        self.rear_window_heat = AC_REAR_WINDOW_HEAT.OFF
        self.sun_sensor = SUN_SENSOR_STATUS.OFF
        self.acc_voltage = 0
        # self._sid_text = get_sid_text_device()

    @property
    def window_max(self):
        return self._window_max

    @window_max.setter
    def window_max(self, value):
        self._window_max = value
        # if self.auto == AC_COOL_MODE_AUTO.ON and self.sun_sensor == SUN_SENSOR_STATUS.OFF:
        #     self.auto = AC_COOL_MODE_AUTO.OFF

    @property
    def fan_speed(self):
        return self._fan_speed

    @fan_speed.setter
    def fan_speed(self, value):
        self._fan_speed = value
        # if self.auto == AC_COOL_MODE_AUTO.ON:
        #     self.auto = AC_COOL_MODE_AUTO.OFF

    def acc_voltage(self, value):
        self._acc_voltage = value
        if self._acc_voltage < settings.ACC_VOLTAGE_THRESHOLD and self.ac_status == AC_STATUS.ON:
            pass
            # commands.INITED_COMMANDS[commands.COMMAND_NAMES.ACStatusOnCommand]()
            # self._sid_text.show_text('Low Battery')


    def get_packed_data(self):
        data = [0x00] * self.DATA_FIELD_LENGTH

        data[0] |= self.ac_status << 7
        data[0] |= self.ac << 6
        data[0] |= (self.fan_speed.state << 0) & 0x0f
        data[0] |= self.cycle << 5
        data[0] |= self.rear_window_heat << 4
        #data[0] |= 1 << 3   # Auto in cycle mode. Nothig to show?

        data[1] |= self.dual << 5
        data[1] |= self.window_max << 4
        data[1] |= self.fan_dir << 0

        data[2] |= self.l_temp.state
        data[3] |= self.r_temp.state

        data[4] |= (self.r_seat_heat.state << 0)
        data[4] |= (self.l_seat_heat.state << 4)
        data[5] |= self.ext_temp.state
        data[6] |= self.auto << 1
        # data[6] |= 1 << 0  # Nothig to show?

        return data


class TempController(BaseController):
    def __init__(self):
        super(TempController, self).__init__(CONTROLLER_TYPES.TEMP)
        self.coolant = 0
        self._int_temp = 0
        self._int_l_temp = 0
        self._int_r_temp = 0
        self._mixed_temp = 0
        self._cooler_temp = 0
        self._sensors_state = {
            settings.TEMP_SENSORS.INT: self._int_temp,
            settings.TEMP_SENSORS.INT_L: self._int_l_temp,
            settings.TEMP_SENSORS.INT_R: self._int_r_temp,
            settings.TEMP_SENSORS.COOLER: self._cooler_temp,
            settings.TEMP_SENSORS.MIXED: self._mixed_temp,
        }

    @property
    def sensors_state(self):
        return self._sensors_state

    @property
    def int_temp(self):
        return self.sensors_state[settings.TEMP_SENSORS.INT]

    def set_temp(self, sensor_name, temp):
        if sensor_name in self._sensors_state:
            self._sensors_state[sensor_name] = temp
        else:
            print("[TempController] Cannot assign temp to sensor: {}".format(sensor_name))


climate_controller = None
temp_controller = None


def get_climate_controller():
    global climate_controller
    if climate_controller is None:
        climate_controller = ClimateController()
    return climate_controller


def get_temp_controller():
    global temp_controller
    if temp_controller is None:
        temp_controller = TempController()
    return temp_controller
