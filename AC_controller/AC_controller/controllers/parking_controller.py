from multimedia_controller.constants import UART_TYPES
from multimedia_controller.settings import F_PARKING_RANGE, R_PARKING_RANGE
from multimedia_controller.controllers.base_controller import BaseController


class FrontParkingController(BaseController):
    def __init__(self,):
        super(FrontParkingController, self).__init__(UART_TYPES.F_PARK)
        self.r = min(F_PARKING_RANGE.R)
        self.rc = min(F_PARKING_RANGE.RC)
        self.lc = min(F_PARKING_RANGE.LC)
        self.l = min(F_PARKING_RANGE.L)

    def get_packed_data(self):
        data = [0x00, 0x00, 0x00, 0x00]
        data[0] = self.l
        data[1] = self.lc
        data[2] = self.rc
        data[3] = self.r
        return data


class RearParkingController(BaseController):
    def __init__(self,):
        super(RearParkingController, self).__init__(UART_TYPES.R_PARK)
        self.r = min(R_PARKING_RANGE.R)
        self.rc = min(R_PARKING_RANGE.RC)
        self.lc = min(R_PARKING_RANGE.LC)
        self.l = min(R_PARKING_RANGE.L)

    def get_packed_data(self):
        data = [0x00, 0x00, 0x00, 0x00]
        data[0] = self.l
        data[1] = self.lc
        data[2] = self.rc
        data[3] = self.r
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