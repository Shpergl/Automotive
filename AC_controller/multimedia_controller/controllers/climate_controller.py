from multimedia_controller import settings
from multimedia_controller.constants import UART_TYPES, AC_CYCLE_MODE, AC_STATUS, AC_COOL_MODE, \
    AC_COOL_MODE_AUTO, AC_DUAL_MODE, AC_WINDOW_MAX, AC_FAN_DIR, AC_REAR_WINDOW_HEAT, CONTROLLER_NAMES
from multimedia_controller.controllers.base_controller import BaseController, SequentialSelector, CycledSelector, \
    BaseStateSelector

from multimedia_controller.settings import FAN_SPEED_RANGE, SEAT_HEAT_RANGE, AC_TEMP_RANGE, EXT_TEMP_RANGE


class ClimateController(BaseController):
    def __init__(self):
        super(ClimateController, self).__init__(UART_TYPES.AC)
        self.ac_status = AC_STATUS.OFF
        self.ac = AC_COOL_MODE.OFF
        self.auto = AC_COOL_MODE_AUTO.OFF
        self.dual = AC_DUAL_MODE.OFF
        self.l_temp = SequentialSelector(AC_TEMP_RANGE, min(AC_TEMP_RANGE))
        self.r_temp = SequentialSelector(AC_TEMP_RANGE, min(AC_TEMP_RANGE))
        self.fan_speed = SequentialSelector(FAN_SPEED_RANGE, min(FAN_SPEED_RANGE))
        self.l_seat_heat = CycledSelector(SEAT_HEAT_RANGE, min(SEAT_HEAT_RANGE))
        self.r_seat_heat = CycledSelector(SEAT_HEAT_RANGE, min(SEAT_HEAT_RANGE))
        self.ext_temp = BaseStateSelector(EXT_TEMP_RANGE, 0)
        self.fan_dir = AC_FAN_DIR.AC_FAN_DIR_UP_DOWN_CENTER
        self.cycle = AC_CYCLE_MODE.EXTERIOR
        self.window_max = AC_WINDOW_MAX.OFF
        self.rear_window_heat = AC_REAR_WINDOW_HEAT.OFF

    def get_packed_data(self):
        data = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]

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
        super(TempController, self).__init__(CONTROLLER_NAMES.TEMP)
        self._int_temp = None
        self._int_l_temp = None
        self._int_r_temp = None
        self._mixed_temp = None
        self._cooler_temp = None
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
