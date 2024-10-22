import time

from AC_controller.can.can_bus import get_CAN_bus
from AC_controller.constants import UART_TYPES, AC_COOL_MODE
from AC_controller.controllers.climate_controller import get_climate_controller
from AC_controller.helpers.observer import Observer
from AC_controller.helpers.utils import chunk_string, ascii_to_hex

TEXT_FOR_EVENT = {
    AC_COOL_MODE.ON: "AC is ON"

}
class SIDTextDevice(Observer):
    RAW_MAX_LEN = 12
    MESSAGES_ORDER = (0x45, 0x04, 0x03, 0x02, 0x01, 0x00)
    TEXT_CONTROL_ID = 0x34c
    TEXT_SHOW_ID = 0x32c
    PACKET_SEND_INTERVAL = 0.01

    def __init__(self):
        self.subscribe(get_climate_controller())
        self._can = get_CAN_bus()
        self._ac_status = None

    def _text_control(self):
        data = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
        data[0] = 0x18  # 0x018 ACC
        data[1] = 0x00  # 0x00 -1,2 rows,0x01 - 2 row, 0x02 - ?
        data[2] = 0x00  # Priority - 0x00 -higher 0xff - lower
        data[3] = 0x23  # Priority - 0x00 -higher 0xff - lower
        self._can.send(self.TEXT_CONTROL_ID, data)

    def _show_text(self, text):
        raw_string = chunk_string(text, self.RAW_MAX_LEN)
        print(raw_string)

        for msg_idx, msg_ord in enumerate(self.MESSAGES_ORDER):
            data = [0x00, 0x96, 0x00, 0x20, 0x20, 0x20, 0x20, 0x20]
            data[0] = msg_ord
            if msg_idx < 3:
                data[2] = 0x81
                chunk_str = chunk_string(raw_string[0], 5)
                chunk_idx = msg_idx
            else:
                data[2] = 0x82
                chunk_str = chunk_string(raw_string[1], 5) if len(raw_string) > 2 else []
                chunk_idx = msg_idx - 3

            if chunk_idx < len(chunk_str):
                for i, c in enumerate(chunk_str[chunk_idx]):
                    data[3 + i] = ascii_to_hex(c)

            self._can.send(self.TEXT_SHOW_ID, data)
            msg_idx += 1
            time.sleep(self.PACKET_SEND_INTERVAL)

    def update(self, subject_type, subject):
        pass
        # if subject_type == UART_TYPES.AC:
        #     self._text_control()
        #     if subject.ac != self._ac_status:
        #         if subject.ac == AC_COOL_MODE.ON:
        #             self._show_text('AC is ON')
        #         else:
        #             self._show_text('AC is OFF')
        #         self._ac_status = subject.ac

