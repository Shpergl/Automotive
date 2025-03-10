from constants import UART_TYPES
from settings import F_PARKING_RANGE, R_PARKING_RANGE
from controllers.base_controller import BaseController

from helpers.utils import scale
from settings import PARKING_SENSOR_VALUES_RANGE


class FrontParkingController(BaseController):
    DATA_FIELD_LENGTH = 4

    def __init__(self,):
        super(FrontParkingController, self).__init__(UART_TYPES.F_PARK)
        self.r = min(F_PARKING_RANGE.R)
        self.rc = min(F_PARKING_RANGE.RC)
        self.lc = min(F_PARKING_RANGE.LC)
        self.l = min(F_PARKING_RANGE.L)

    # def get_packed_data(self):
    #     data = [0x00] * self.DATA_FIELD_LENGTH
    #     d1 = scale(PARKING_SENSOR_VALUES_RANGE, F_PARKING_RANGE.L, self.l*10)
    #     d2 = scale(PARKING_SENSOR_VALUES_RANGE, F_PARKING_RANGE.LC, self.lc*10)
    #     d3 = scale(PARKING_SENSOR_VALUES_RANGE, F_PARKING_RANGE.RC, self.rc*10)
    #     d4 = scale(PARKING_SENSOR_VALUES_RANGE, F_PARKING_RANGE.R, self.r*10)
    #     data[0] = d1
    #     data[1] = d2
    #     data[2] = d3
    #     data[3] = d4
    #     return data

    def get_packed_data(self):
        data = [0x00] * 2
        data[0] = 100
        data[1] = 100
        return data

class RearParkingController(BaseController):
    DATA_FIELD_LENGTH = 4

    def __init__(self,):
        super(RearParkingController, self).__init__(UART_TYPES.R_PARK)
        self.r = min(R_PARKING_RANGE.R)
        self.rc = min(R_PARKING_RANGE.RC)
        self.lc = min(R_PARKING_RANGE.LC)
        self.l = min(R_PARKING_RANGE.L)

    def get_packed_data(self):
        data = [0x00] * self.DATA_FIELD_LENGTH
        data[0] = scale(PARKING_SENSOR_VALUES_RANGE, R_PARKING_RANGE.L, self.l*10)
        data[1] = scale(PARKING_SENSOR_VALUES_RANGE, R_PARKING_RANGE.LC, self.lc*10)
        data[2] = scale(PARKING_SENSOR_VALUES_RANGE, R_PARKING_RANGE.RC, self.rc*10)
        data[3] = scale(PARKING_SENSOR_VALUES_RANGE, R_PARKING_RANGE.R, self.r*10)
        return data


front_parking_controller = None
rear_parking_controller = None


def get_front_parking_controller():
    global front_parking_controller
    if front_parking_controller is None:
        front_parking_controller = FrontParkingController()
    return front_parking_controller


def get_rear_parking_controller():
    global rear_parking_controller
    if rear_parking_controller is None:
        rear_parking_controller = RearParkingController()
    return rear_parking_controller
