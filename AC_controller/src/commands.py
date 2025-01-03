import time

from constants import (UART_COMMANDS, AC_COOL_MODE, AC_STATUS, AC_DUAL_MODE, AC_CYCLE_MODE,
                                             AC_WINDOW_MAX, AC_COOL_MODE_AUTO, AC_FAN_DIR, AC_REAR_WINDOW_HEAT)
from controllers.climate_controller import get_climate_controller
from helpers.utils import unpack_fan_dir, pack_fan_dir
from settings import UART_COMMAND_DEBOUNCE_TIMEOUT, FAN_SPEED_RANGE, CAN_COMMAND_DEBOUNCE_TIMEOUT, DUBUG_MODE


class BaseCommand:
    def __init__(self):
        self._debounce_time = 0
        self._debounce_timout = 0

    def __call__(self, *args, **kwargs):
        if (time.ticks_ms() - self._debounce_time) < self._debounce_timout or not self._validate(*args, **kwargs):
            return
        self._execute(*args, **kwargs)
        self._debounce_time = time.ticks_ms()

    def _validate(self, *args, **kwargs):
        pass

    def _execute(self, *args, **kwargs):
        pass


class BaseUartCommand(BaseCommand):
    def __init__(self):
        super(BaseUartCommand, self).__init__()
        self._debounce_timout = UART_COMMAND_DEBOUNCE_TIMEOUT
        self._controller = None

    def _validate(self):
        return True


class BaseCanCommand(BaseCommand):
    DATA_FIELD_LENGTH = 8

    def __init__(self):
        super(BaseCanCommand, self).__init__()
        self._debounce_timout = CAN_COMMAND_DEBOUNCE_TIMEOUT
        self._cached_data = [0x00] * self.DATA_FIELD_LENGTH

    def _validate(self, msg):
        if msg.id is None or msg.data is None:
            print("[CAN command failed] cannot execute. "
                  "Missing information message: {}".format(msg))
            return False
        return True

    def _execute(self, msg):
        if DUBUG_MODE:
            print("[CAN command] {}/{} executing".format(self._id, msg.data))

    def build(self):
        pass


class StubCommand(BaseUartCommand):
    def __init__(self):
        super(StubCommand, self).__init__()

    def _execute(self):
        pass


class ACSeatHeatLCommand(BaseUartCommand):
    def __init__(self):
        super(ACSeatHeatLCommand, self).__init__()
        self._controller = get_climate_controller()
        print('ACSeatHeatLCommand init()')

    def _execute(self):
        self._controller.l_seat_heat.next_state()
        self._controller.send_update()


class ACSeatHeatRCommand(BaseUartCommand):
    def __init__(self):
        super(ACSeatHeatRCommand, self).__init__()
        self._controller = get_climate_controller()
        print('ACSeatHeatRCommand init()')

    def _execute(self):
        self._controller.r_seat_heat.next_state()
        self._controller.send_update()


class ACCycleOnCommand(BaseUartCommand):
    def __init__(self):
        super(ACCycleOnCommand, self).__init__()
        self._controller = get_climate_controller()
        print('ACCycleOnCommand init')

    def _execute(self):
        if self._controller.cycle == AC_CYCLE_MODE.EXTERIOR:
            self._controller.cycle = AC_CYCLE_MODE.INTERIOR
        else:
            self._controller.cycle = AC_CYCLE_MODE.EXTERIOR
        self._controller.send_update()


class ACRearWindowHeatOnCommand(BaseUartCommand):
    def __init__(self):
        super(ACRearWindowHeatOnCommand, self).__init__()
        self._controller = get_climate_controller()
        print('ACRearWindowHeatOnCommand init')

    def _execute(self):
        if self._controller.rear_window_heat == AC_REAR_WINDOW_HEAT.OFF:
            self._controller.rear_window_heat = AC_REAR_WINDOW_HEAT.ON
        else:
            self._controller.rear_window_heat = AC_REAR_WINDOW_HEAT.OFF
        self._controller.send_update()


class ClimateCommand(BaseUartCommand):
    def __init__(self):
        super(ClimateCommand, self).__init__()
        self._controller = get_climate_controller()

    def _validate(self):
        return self._controller.ac_status == AC_STATUS.ON


class ACStatusOnCommand(ClimateCommand):
    def __init__(self):
        super(ACStatusOnCommand, self).__init__()
        self._prev_fan_speed = None
        self._prev_ac_state = None
        print('ACStatusOnCommand init')

    def _execute(self):
        if self._controller.ac_status == AC_STATUS.ON:
            self._controller.ac_status = AC_STATUS.OFF
            self._prev_fan_speed = self._controller.fan_speed.state
            self._prev_ac_state = self._controller.ac
            self._controller.fan_speed.state = min(FAN_SPEED_RANGE)
            self._controller.ac = AC_COOL_MODE.OFF
        else:
            self._controller.ac_status = AC_STATUS.ON
            if self._prev_fan_speed is not None:
                self._controller.fan_speed.state = self._prev_fan_speed
                self._prev_fan_speed = None
            if self._prev_ac_state is not None:
                self._controller.ac = self._prev_ac_state
                self._prev_ac_state = None
        self._controller.send_update()

    def _validate(self):
        return True


class ACDualOnCommand(ClimateCommand):
    def __init__(self):
        super(ACDualOnCommand, self).__init__()
        print('ACDualOnCommand init')

    def _execute(self):
        if self._controller.dual == AC_DUAL_MODE.OFF:
            self._controller.dual = AC_DUAL_MODE.ON
        else:
            self._controller.dual = AC_DUAL_MODE.OFF
        self._controller.send_update()


class ACWindowMaxOnCommand(ClimateCommand):
    def __init__(self):
        super(ACWindowMaxOnCommand, self).__init__()
        self._prev_fan_dir = None
        self._prev_fan_speed = None
        print('ACWindowMaxOnCommand init')

    def _execute(self):
        if self._controller.window_max == AC_WINDOW_MAX.OFF:
            self._controller.window_max = AC_WINDOW_MAX.ON
            self._prev_fan_dir = self._controller.fan_dir
            self._prev_fan_speed = self._controller.fan_speed.state
            self._controller.fan_dir = AC_FAN_DIR.AC_FAN_DIR_FRONT_WINDOW
            self._controller.fan_speed.state = max(FAN_SPEED_RANGE)
        else:
            self._controller.window_max = AC_WINDOW_MAX.OFF
            if self._prev_fan_dir is not None:
                self._controller.fan_dir = self._prev_fan_dir
                self._prev_fan_dir = None
            if self._prev_fan_speed is not None:
                self._controller.fan_speed.state = self._prev_fan_speed
                self._prev_fan_speed = None
        self._controller.send_update()


class ACAutoOnCommand(ClimateCommand):
    def __init__(self):
        super(ACAutoOnCommand, self).__init__()
        print('ACAutoOnCommand init')

    def _execute(self):
        if self._controller.auto == AC_COOL_MODE_AUTO.OFF:
            if self._controller.window_max == AC_WINDOW_MAX.ON:
                INITED_COMMANDS[COMMAND_NAMES.ACWindowMaxOnCommand]()
            self._controller.auto = AC_COOL_MODE_AUTO.ON
        else:
            self._controller.auto = AC_COOL_MODE_AUTO.OFF
        self._controller.send_update()


class ACOnCommand(ClimateCommand):
    def __init__(self):
        super(ACOnCommand, self).__init__()
        print('ACOnCommand init()')

    def _execute(self):
        if self._controller.ac == AC_COOL_MODE.OFF:
            self._controller.ac = AC_COOL_MODE.ON
        else:
            self._controller.ac = AC_COOL_MODE.OFF
        self._controller.send_update()


class ACFanDirUpCommand(ClimateCommand):
    def __init__(self):
        super(ACFanDirUpCommand, self).__init__()
        print('ACFanDirUpCommand init()')

    def _execute(self):
        up_state, middle_state, down_state = unpack_fan_dir(self._controller.fan_dir)
        up = 0 if up_state == 1 else 1
        self._controller.fan_dir = pack_fan_dir(up, middle_state, down_state)
        self._controller.send_update()


class ACFanDirMiddleCommand(ClimateCommand):
    def __init__(self):
        super(ACFanDirMiddleCommand, self).__init__()
        print('ACFanDirMiddleCommand init()')

    def _execute(self):
        up_state, middle_state, down_state = unpack_fan_dir(self._controller.fan_dir)
        middle = 0 if middle_state == 1 else 1
        self._controller.fan_dir = pack_fan_dir(up_state, middle, down_state)
        self._controller.send_update()


class ACFanDirDownCommand(ClimateCommand):
    def __init__(self):
        super(ACFanDirDownCommand, self).__init__()
        print('ACFanDirDownCommand init()')

    def _execute(self):
        up_state, middle_state, down_state = unpack_fan_dir(self._controller.fan_dir)
        down = 0 if down_state == 1 else 1
        self._controller.fan_dir = pack_fan_dir(up_state, middle_state, down)
        self._controller.send_update()


class ACIncFanSpeedCommand(ClimateCommand):
    def __init__(self):
        super(ACIncFanSpeedCommand, self).__init__()
        print('ACIncFanSpeedCommand init()')

    def _execute(self):
        self._controller.fan_speed.next_state()
        self._controller.send_update()


class ACDecFanSpeedCommand(ClimateCommand):
    def __init__(self):
        super(ACDecFanSpeedCommand, self).__init__()
        print('ACDecFanSpeedCommand init()')

    def _execute(self):
        if self._controller.window_max == AC_WINDOW_MAX.ON:
            return
        self._controller.fan_speed.prev_state()
        self._controller.send_update()


class ACIncLTempCommand(ClimateCommand):
    def __init__(self):
        super(ACIncLTempCommand, self).__init__()
        print('ACIncLTempCommand init()')

    def _execute(self):
        self._controller.l_temp.next_state()
        if self._controller.dual == AC_DUAL_MODE.ON:
            self._controller.r_temp.state = self._controller.l_temp.state
        self._controller.send_update()


class ACDecLTempCommand(ClimateCommand):
    def __init__(self):
        super(ACDecLTempCommand, self).__init__()
        print('ACDecLTempCommand init()')

    def _execute(self):
        self._controller.l_temp.prev_state()
        if self._controller.dual == AC_DUAL_MODE.ON:
            self._controller.r_temp.state = self._controller.l_temp.state
        self._controller.send_update()


class ACIncRTempCommand(ClimateCommand):
    def __init__(self):
        super(ACIncRTempCommand, self).__init__()
        print('ACIncRTempCommand init()')

    def _execute(self):
        self._controller.r_temp.next_state()
        if self._controller.dual == AC_DUAL_MODE.ON:
            self._controller.l_temp.state = self._controller.r_temp.state
        self._controller.send_update()


class ACDecRTempCommand(ClimateCommand):
    def __init__(self):
        super(ACDecRTempCommand, self).__init__()
        print('ACDecRTempCommand init()')

    def _execute(self):
        self._controller.r_temp.prev_state()
        if self._controller.dual == AC_DUAL_MODE.ON:
            self._controller.l_temp.state = self._controller.r_temp.state
        self._controller.send_update()


class COMMAND_NAMES:
    ACOnCommand = 'ACOnCommand'
    ACStatusOnCommand = 'ACStatusOnCommand'
    ACAutoOnCommand = 'ACAutoOnCommand'
    ACDualOnCommand = 'ACDualOnCommand'
    ACIncLTempCommand = 'ACIncLTempCommand'
    ACDecLTempCommand = 'ACDecLTempCommand'
    ACIncRTempCommand = 'ACIncRTempCommand'
    ACDecRTempCommand = 'ACDecRTempCommand'
    ACIncFanSpeedCommand = 'ACIncFanSpeedCommand'
    ACDecFanSpeedCommand = 'ACDecFanSpeedCommand'
    ACSeatHeatLCommand = 'ACSeatHeatLCommand'
    ACSeatHeatRCommand = 'ACSeatHeatRCommand'
    ACCycleOnCommand = 'ACCycleOnCommand'
    ACWindowMaxOnCommand = 'ACWindowMaxOnCommand'
    ACFanDirUpCommand = 'ACFanDirUpCommand'
    ACFanDirMiddleCommand = 'ACFanDirMiddleCommand'
    ACFanDirDownCommand = 'ACFanDirDownCommand'
    ACRearWindowHeatOnCommand = 'ACRearWindowHeatOnCommand'
    StubCommand = 'StubCommand'


COMMANDS = (
    ACOnCommand,
    ACStatusOnCommand,
    ACAutoOnCommand,
    ACDualOnCommand,
    ACIncLTempCommand,
    ACDecLTempCommand,
    ACIncRTempCommand,
    ACDecRTempCommand,
    ACIncFanSpeedCommand,
    ACDecFanSpeedCommand,
    ACSeatHeatLCommand,
    ACSeatHeatRCommand,
    ACCycleOnCommand,
    ACWindowMaxOnCommand,
    ACFanDirUpCommand,
    ACFanDirMiddleCommand,
    ACFanDirDownCommand,
    ACRearWindowHeatOnCommand,
    StubCommand,
)


INITED_COMMANDS = {c.__name__: c() for c in COMMANDS}


UARTCmdHandlers = {
     UART_COMMANDS.AC_ON: INITED_COMMANDS[COMMAND_NAMES.ACOnCommand],
     UART_COMMANDS.AC_STATUS_ON: INITED_COMMANDS[COMMAND_NAMES.ACStatusOnCommand],
     UART_COMMANDS.AC_MODE_AUTO_ON: INITED_COMMANDS[COMMAND_NAMES.ACAutoOnCommand],
     UART_COMMANDS.DUAL_MODE_ON: INITED_COMMANDS[COMMAND_NAMES.ACDualOnCommand],
     UART_COMMANDS.L_TEMP_INC: INITED_COMMANDS[COMMAND_NAMES.ACIncLTempCommand],
     UART_COMMANDS.L_TEMP_DEC: INITED_COMMANDS[COMMAND_NAMES.ACDecLTempCommand],
     UART_COMMANDS.R_TEMP_INC: INITED_COMMANDS[COMMAND_NAMES.ACIncRTempCommand],
     UART_COMMANDS.R_TEMP_DEC: INITED_COMMANDS[COMMAND_NAMES.ACDecRTempCommand],
     UART_COMMANDS.FAN_SPEED_INC: INITED_COMMANDS[COMMAND_NAMES.ACIncFanSpeedCommand],
     UART_COMMANDS.FAN_SPEED_DEC: INITED_COMMANDS[COMMAND_NAMES.ACDecFanSpeedCommand],
     UART_COMMANDS.L_SEAT_HEAT_SWITCH: INITED_COMMANDS[COMMAND_NAMES.ACSeatHeatLCommand],
     UART_COMMANDS.R_SEAT_HEAT_SWITCH: INITED_COMMANDS[COMMAND_NAMES.ACSeatHeatRCommand],
     UART_COMMANDS.CYCLE_MODE_ON: INITED_COMMANDS[COMMAND_NAMES.ACCycleOnCommand],
     UART_COMMANDS.WINDOW_MAX_ON: INITED_COMMANDS[COMMAND_NAMES.ACWindowMaxOnCommand],
     UART_COMMANDS.FAN_DIR_WINDOW: INITED_COMMANDS[COMMAND_NAMES.ACFanDirUpCommand],
     UART_COMMANDS.FAN_DIR_MIDDLE: INITED_COMMANDS[COMMAND_NAMES.ACFanDirMiddleCommand],
     UART_COMMANDS.FAN_DIR_DOWN: INITED_COMMANDS[COMMAND_NAMES.ACFanDirDownCommand],
     UART_COMMANDS.REAR_WINDOW_HEAT_ON: INITED_COMMANDS[COMMAND_NAMES.ACRearWindowHeatOnCommand],
     UART_COMMANDS.STUB_REQUEST: INITED_COMMANDS[COMMAND_NAMES.StubCommand],
}
