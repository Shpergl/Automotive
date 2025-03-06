import time
from micropython import const

from constants import (UART_COMMANDS, AC_COOL_MODE, AC_STATUS, AC_DUAL_MODE, AC_CYCLE_MODE, AC_WINDOW_MAX,
                       AC_COOL_MODE_AUTO, AC_FAN_DIR, AC_REAR_WINDOW_HEAT, CAN_COMMANDS_IDS, CAN_COMMANDS_NAMES)
from controllers.door_controller import get_door_controller
from controllers.climate_controller import get_climate_controller, get_temp_controller
from controllers.parking_controller import get_front_parking_controller, get_rear_parking_controller
from helpers.utils import unpack_fan_dir, pack_fan_dir, get_16_bit_hex
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
        self._id = None

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

class DoorStatusCommand(BaseCanCommand):
    """
      ID  | byte0 | byte1 | byte2 | byte3 | byte4 | byte5 | byte6 | byte7 |
    0x320 | STATE | DOOR  | BELT  |   -   | BULBS |   -   |   -   |   -   |

      byte  |   bit7   |   bit6   |   bit5   |   bit4   |   bit3   |   bit2   |   bit1   |   bit0   |
      STATE | CHANGED  |
      DOOR  |  LOCKED  |    FL    |    FR    |    RL    |    RR    |  TRUNK   |
    """
    def __init__(self):
        super(DoorStatusCommand, self).__init__()
        self._id = CAN_COMMANDS_IDS.DOOR_STATUS  # 0x320
        self._controller = get_door_controller()

    def _execute(self, msg):
        super(DoorStatusCommand, self)._execute(msg)
        data = msg.data
        changed = data[0] >> 7 & 0x01
        if changed:
            door_state = data[1]
            self._controller.locked = door_state >> 7 & 0x01
            self._controller.fl = door_state >> 6 & 0x01
            self._controller.fr = door_state >> 5 & 0x01
            self._controller.rl = door_state >> 4 & 0x01
            self._controller.rl = door_state >> 3 & 0x01
            self._controller.trunk = door_state >> 2 & 0x01
            self._controller.send_update()


class ExtTempCommand(BaseCanCommand):
    """
      ID  | byte0  |   byte1   |   byte2   |   byte3    |   byte4  | byte5 | byte6 | byte7 |
    0x7a0 | STATUS | AVGTEMP1  | AVGTEMP0  |  RAWTEMP1  | RAWTEMP0 |   -   |   -   |   -   |
    AVGTEMP1 + AVGTEMP0 = Temp with 1 degree precision (16 digits)
    RAWTEMP1 + RAWTEMP0 = Temp with 0.5 degree precision (16 digits)
    STATUS: 0x30 - STATUS Inside temp, STATUS Outside temp -> 0x00
    """
    def __init__(self):
        super(ExtTempCommand, self).__init__()
        self._id = CAN_COMMANDS_IDS.OUTSIDE_TEMP  # 0x7a0
        self._controller = get_climate_controller()

    def _execute(self, msg):
        super(ExtTempCommand, self)._execute(msg)
        data = msg.data
        avg_temp = get_16_bit_hex(data[1], data[2])
        real_avg_temp = int((avg_temp / 10) - 40)
        self._controller.ext_temp.state = real_avg_temp
        self._controller.send_update()
        if DUBUG_MODE:
            print('real_avg_temp: {}'.format(real_avg_temp))


class ParkingCommand(BaseCanCommand):
    """
    Custom CAN command
         ID   | byte0 | byte1 | byte2 | byte3 |  byte4  | byte5   |  byte6  |   byte7  |
       0x439  |   RL  |  RLC  |  RRC  |  RR   |    FL   |   FLC   |   FRC   |    FR    |
       """
    def __init__(self):
        super(ParkingCommand, self).__init__()
        self._id = CAN_COMMANDS_IDS.SPA_DISTANCE  # 0x439
        self._f_controller = get_front_parking_controller()
        self._r_controller = get_rear_parking_controller()

    def _execute(self, msg):
        super(ParkingCommand, self)._execute(msg)
        data = msg.data
        self._r_controller.l = int(data[0])
        self._r_controller.lc = int(data[1])
        self._r_controller.rc = int(data[2])
        self._r_controller.r = int(data[3])
        self._r_controller.send_update()

        self._f_controller.l = int(data[4])
        self._f_controller.lc = int(data[5])
        self._f_controller.rc = int(data[6])
        self._f_controller.r = int(data[7])
        self._f_controller.send_update()
        print('Raw data: {}\n, {}, {}, {}, {}, {}, {}, {}, {}\n'.format(msg.data, int(data[0]), int(data[1]), int(data[2]),
                                                        int(data[3]), int(data[4]), int(data[5]), int(data[6]),
                                                        int(data[7])))


class ACCDiceCommand(BaseCanCommand):
    """
      ID  | byte0  |   byte1   |   byte2   |   byte3    |   byte4  | byte5 | byte6 | byte7 |
    0x530 |   -    |    ACC    |      -    |  ACPRESS  |      -    |   -   |   -   |   -   |

    byte  |   bit7   |   bit6   |   bit5   |   bit4   |   bit3   |   bit2   |   bit1   |   bit0   |
    ACC   |  -      |     -    |    -     |   -       |    -     |   ACCON  |     -    |     -    |

    ACPRESS - units in bar
    Interval 1 sec
    """
    def __init__(self):
        super(ACCDiceCommand, self).__init__()
        self._id = CAN_COMMANDS_IDS.ACC_DICE  # 0x530

    def _execute(self, msg):
        super(ACCDiceCommand, self)._execute(msg)
        data = msg.data
        acc_on = data[1] >> 2 & 0x01
        ac_pressure = data[3]  # bar
        if DUBUG_MODE:
            print("acc_on: {}, ac_pressure: {}".format(acc_on, ac_pressure))


class CoolantTempAndAirPressureCommand(BaseCanCommand):
    """
      ID  | byte0  |   byte1   |   byte2   |   byte3    |   byte4  | byte5 | byte6 | byte7 |
    0x5c0 |   -    |  COOLANT  |   PRES1   |  PRES0     |     -    |   -   |   -   |   -   |

    COOLANT = Coolant temp - 40 (8 bit)
    PRES1 + PRES0 = Am,bient air pressure (16 bits) [hPa]
    """
    COOLANT_TEMP_CONSTANT = const(40)

    def __init__(self):
        super(CoolantTempAndAirPressureCommand, self).__init__()
        self._id = CAN_COMMANDS_IDS.COOLANT_TEMP_AIR_PRESSURE  # 0x5c0
        self._temp_controller = get_temp_controller()

    def _execute(self, msg):
        super(CoolantTempAndAirPressureCommand, self)._execute(msg)
        data = msg.data
        coolant = int(data[1]) - self.COOLANT_TEMP_CONSTANT
        air_pressure = get_16_bit_hex(data[2], data[3])
        self._temp_controller.coolant = coolant
        self._temp_controller.send_update()
        if DUBUG_MODE:
            print("Coolant: {}, AirPress: {}".format(coolant, air_pressure))


class ACCCommand(BaseCanCommand):
    """
      ID  | byte0   |   byte1   |   byte2   |   byte3    |   byte4  | byte5  | byte6 | byte7 |
    0x520 |  STATE  |    ACC    |      -    |  ACPRESS  |      -    |  TEMP  |   -   |   -   |

    byte    |   bit7   |   bit6   |   bit5   |   bit4   |   bit3   |   bit2   |   bit1   |   bit0   |
    STATE   | CHANGED  |     -    |    -     |   -      |    -     |    -     |     -    |     -    |
     ACC    | COMPRESSOR | REARHEAT |    -     |   -      |    -     |    -     |     -    |     -    |

    TEMP - inside temperature, units in degrees Celsius ( -40 from decoded value)
    Interval 1 sec
    """
    INT_TEMP_CONSTANT = const(40)

    def __init__(self):
        super(ACCCommand, self).__init__()
        self._id = CAN_COMMANDS_IDS.ACC_AND_INSIDE_TEMP  # 0x520
        self._climate_controller = get_climate_controller()
        self._temp_controller = get_temp_controller()
        self._cached_data = None

    def _execute(self, msg):
        super(ACCCommand, self)._execute(msg)
        data = msg.data
        changed = data[0] >> 7 & 0x01
        if changed:
            rear_heat = data[1] >> 6 & 0x01
            compressor_on = data[1] >> 7 & 0x01
            temp = data[5] - self.INT_TEMP_CONSTANT
            if DUBUG_MODE:
                print("compressor_on: {}, temp: {}, rear_heat: {}".format(compressor_on, temp, rear_heat))

    def build(self):
        data = [0x00] * 8
        data[1] |= self._climate_controller.rear_window_heat << 6
        data[1] |= self._climate_controller.ac << 7
        data[5] = int(self._temp_controller.int_temp) + self.INT_TEMP_CONSTANT

        data[0] |= bool(data[1:] != self._cached_data[1:]) << 7
        self._cached_data = data

        return self._id, data


CANCmdHandlers = {
    CAN_COMMANDS_IDS.DOOR_STATUS: DoorStatusCommand(),
    CAN_COMMANDS_IDS.OUTSIDE_TEMP: ExtTempCommand(),
    CAN_COMMANDS_IDS.SPA_DISTANCE: ParkingCommand(),
    CAN_COMMANDS_IDS.ACC_DICE: ACCDiceCommand(),
    CAN_COMMANDS_IDS.ACC_AND_INSIDE_TEMP: ACCCommand(),
    CAN_COMMANDS_IDS.COOLANT_TEMP_AIR_PRESSURE: CoolantTempAndAirPressureCommand(),
    #CAN_COMMANDS_IDS.SID_BEEP_REQUEST: DummyCommand(),
    # CAN_COMMANDS_IDS.LIGHT_DIMMER_LIGHT_SENSOR: DummyCommand(),
}
