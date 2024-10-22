from AC_controller.constants import DOOR_STATUS, UART_TYPES, DOOR_HEX_VALUE
from AC_controller.controllers.base_controller import BaseController


class DoorController(BaseController):
    def __init__(self,):
        super(DoorController, self).__init__(UART_TYPES.DOOR)
        self.fl = DOOR_STATUS.CLOSE
        self.fr = DOOR_STATUS.CLOSE
        self.rl = DOOR_STATUS.CLOSE
        self.rr = DOOR_STATUS.CLOSE
        self.trunk = DOOR_STATUS.CLOSE

    def get_packed_data(self):
        data = [0x00]
        if self.trunk == DOOR_STATUS.OPEN:
            data[0] |= DOOR_HEX_VALUE.TRUNK
        if self.rl == DOOR_STATUS.OPEN:
            data[0] |= DOOR_HEX_VALUE.RL
        if self.rr == DOOR_STATUS.OPEN:
            data[0] |= DOOR_HEX_VALUE.RR
        if self.fl == DOOR_STATUS.OPEN:
            data[0] |= DOOR_HEX_VALUE.FL
        if self.fr == DOOR_STATUS.OPEN:
            data[0] |= DOOR_HEX_VALUE.FR
        return data


door_controller = None


def get_door_controller():
    global door_controller
    if door_controller is None:
        door_controller = DoorController()
    return door_controller
