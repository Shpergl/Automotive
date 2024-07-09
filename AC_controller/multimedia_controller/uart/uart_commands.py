import time

from multimedia_controller.constants import (UART_COMMANDS, AC_COOL_MODE, AC_STATUS, AC_DUAL_MODE, AC_CYCLE_MODE,
                                             AC_WINDOW_MAX, AC_COOL_MODE_AUTO, AC_FAN_DIR, AC_REAR_WINDOW_HEAT)
from multimedia_controller.controllers.climate_controller import get_climate_controller
from multimedia_controller.helpers.utils import unpack_fan_dir, pack_fan_dir
from multimedia_controller.settings import UART_DEBOUNCE_TIMEOUT, FAN_SPEED_RANGE


class BaseCommand:
    def __init__(self):
        self._debounce_time = 0
        self._debounce_timout = UART_DEBOUNCE_TIMEOUT
        self._controller = None

    def __call__(self, *args, **kwargs):
        if (time.ticks_ms() - self._debounce_time) < self._debounce_timout or not self._validate():
            return
        self._execute()
        self._debounce_time = time.ticks_ms()

    def _validate(self):
        return True

    def _execute(self):
        pass


class StubCommand(BaseCommand):
    def _execute(self):
        pass


class ACSeatHeatLCommand(BaseCommand):
    def __init__(self):
        super(ACSeatHeatLCommand, self).__init__()
        self._controller = get_climate_controller()
        print('ACSeatHeatLCommand init()')

    def _execute(self):
        self._controller.l_seat_heat.next_state()
        self._controller.send_update()


class ACSeatHeatRCommand(BaseCommand):
    def __init__(self):
        super(ACSeatHeatRCommand, self).__init__()
        self._controller = get_climate_controller()
        print('ACSeatHeatRCommand init()')

    def _execute(self):
        self._controller.r_seat_heat.next_state()
        self._controller.send_update()


class ACCycleOnCommand(BaseCommand):
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


class ACRearWindowHeatOnCommand(BaseCommand):
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


class ClimateCommand(BaseCommand):
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
            self._controller.fan_speed.set_state(min(FAN_SPEED_RANGE))
            self._controller.ac = AC_COOL_MODE.OFF
        else:
            self._controller.ac_status = AC_STATUS.ON
            if self._prev_fan_speed is not None:
                self._controller.fan_speed.set_state(self._prev_fan_speed)
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
            self._controller.fan_speed.set_state(max(FAN_SPEED_RANGE))
        else:
            self._controller.window_max = AC_WINDOW_MAX.OFF
            if self._prev_fan_dir is not None:
                self._controller.fan_dir = self._prev_fan_dir
                self._prev_fan_dir = None
            if self._prev_fan_speed is not None:
                self._controller.fan_speed.set_state(self._prev_fan_speed)
                self._prev_fan_speed = None
        self._controller.send_update()


class ACAutoOnCommand(ClimateCommand):
    def __init__(self):
        super(ACAutoOnCommand, self).__init__()
        print('ACAutoOnCommand init')

    def _execute(self):
        if self._controller.auto == AC_COOL_MODE_AUTO.OFF:
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
            self._controller.r_temp.set_state(self._controller.l_temp.state)
        self._controller.send_update()


class ACDecLTempCommand(ClimateCommand):
    def __init__(self):
        super(ACDecLTempCommand, self).__init__()
        print('ACDecLTempCommand init()')

    def _execute(self):
        self._controller.l_temp.prev_state()
        if self._controller.dual == AC_DUAL_MODE.ON:
            self._controller.r_temp.set_state(self._controller.l_temp.state)
        self._controller.send_update()


class ACIncRTempCommand(ClimateCommand):
    def __init__(self):
        super(ACIncRTempCommand, self).__init__()
        print('ACIncRTempCommand init()')

    def _execute(self):
        self._controller.r_temp.next_state()
        if self._controller.dual == AC_DUAL_MODE.ON:
            self._controller.l_temp.set_state(self._controller.r_temp.state)
        self._controller.send_update()


class ACDecRTempCommand(ClimateCommand):
    def __init__(self):
        super(ACDecRTempCommand, self).__init__()
        print('ACDecRTempCommand init()')

    def _execute(self):
        self._controller.r_temp.prev_state()
        if self._controller.dual == AC_DUAL_MODE.ON:
            self._controller.l_temp.set_state(self._controller.r_temp.state)
        self._controller.send_update()


UARTCmdHandlers = {
     UART_COMMANDS.AC_ON: ACOnCommand(),
     UART_COMMANDS.AC_STATUS_ON: ACStatusOnCommand(),
     UART_COMMANDS.AC_MODE_AUTO_ON: ACAutoOnCommand(),
     UART_COMMANDS.DUAL_MODE_ON: ACDualOnCommand(),
     UART_COMMANDS.L_TEMP_INC: ACIncLTempCommand(),
     UART_COMMANDS.L_TEMP_DEC: ACDecLTempCommand(),
     UART_COMMANDS.R_TEMP_INC: ACIncRTempCommand(),
     UART_COMMANDS.R_TEMP_DEC: ACDecRTempCommand(),
     UART_COMMANDS.FAN_SPEED_INC: ACIncFanSpeedCommand(),
     UART_COMMANDS.FAN_SPEED_DEC: ACDecFanSpeedCommand(),
     UART_COMMANDS.L_SEAT_HEAT_SWITCH: ACSeatHeatLCommand(),
     UART_COMMANDS.R_SEAT_HEAT_SWITCH: ACSeatHeatRCommand(),
     UART_COMMANDS.CYCLE_MODE_ON: ACCycleOnCommand(),
     UART_COMMANDS.WINDOW_MAX_ON: ACWindowMaxOnCommand(),
     UART_COMMANDS.FAN_DIR_WINDOW: ACFanDirUpCommand(),
     UART_COMMANDS.FAN_DIR_MIDDLE: ACFanDirMiddleCommand(),
     UART_COMMANDS.FAN_DIR_DOWN: ACFanDirDownCommand(),
     UART_COMMANDS.REAR_WINDOW_HEAT_ON: ACRearWindowHeatOnCommand(),
     UART_COMMANDS.STUB_REQUEST: StubCommand(),
}
