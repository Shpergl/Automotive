import time
from micropython import const

from constants import CAN_COMMANDS_IDS, CAN_COMMANDS_NAMES
from controllers.door_controller import get_door_controller
from controllers.climate_controller import get_climate_controller
from controllers.parking_controller import (get_front_parking_controller,
                                                                  get_rear_parking_controller)
from helpers.utils import get_16_bit_hex, get_24_bit_hex
from settings import CAN_COMMAND_DEBOUNCE_TIMEOUT, DUBUG_MODE

from controllers.climate_controller import get_temp_controller


class BaseCommand:
    DATA_FIELD_LENGTH = 8

    def __init__(self):
        self._id = 0
        self._debounce_time = 0
        self._debounce_timout = CAN_COMMAND_DEBOUNCE_TIMEOUT
        self._cached_data = [0x00] * self.DATA_FIELD_LENGTH

    def __call__(self, *args, **kwargs):
        if (time.ticks_ms() - self._debounce_time) < self._debounce_timout or not self._validate(*args, **kwargs):
            return
        self._execute(*args, **kwargs)
        self._debounce_time = time.ticks_ms()

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


class DummyCommand(BaseCommand):
    def _execute(self, msg):
        super(DummyCommand, self)._execute(msg)
        unpacked_data = [hex(x) for x in bytearray(msg.get('data'))]
        print("{} ({}), data: {}".format(CAN_COMMANDS_NAMES.get(msg.get('id')), hex(msg.get('id')), unpacked_data))


class DoorStatusCommand(BaseCommand):
    """
      ID  | byte0 | byte1 | byte2 | byte3 | byte4 | byte5 | byte6 | byte7 |
    0x320 | STATE | DOOR  | BELT  |   -   | BULBS |   -   |   -   |   -   |

      byte  |   bit7   |   bit6   |   bit5   |   bit4   |   bit3   |   bit2   |   bit1   |   bit0   |
      STATE | CHANGED  |
      DOOR  |  LOCKED  |    FL    |    FR    |    RL    |    RR    |  TRUNK   |
    """
    def __init__(self):
        super(DoorStatusCommand, self).__init__()
        self._id = 0x320
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


class ExtTempCommand(BaseCommand):
    """
      ID  | byte0  |   byte1   |   byte2   |   byte3    |   byte4  | byte5 | byte6 | byte7 |
    0x7a0 | STATUS | AVGTEMP1  | AVGTEMP0  |  RAWTEMP1  | RAWTEMP0 |   -   |   -   |   -   |
    AVGTEMP1 + AVGTEMP0 = Temp with 1 degree precision (16 digits)
    RAWTEMP1 + RAWTEMP0 = Temp with 0.5 degree precision (16 digits)
    STATUS: 0x30 - STATUS Inside temp, STATUS Outside temp -> 0x00
    """
    def __init__(self):
        super(ExtTempCommand, self).__init__()
        self._id = 0x7a0
        self._controller = get_climate_controller()

    def _execute(self, msg):
        super(ExtTempCommand, self)._execute(msg)
        data = msg.data
        avg_temp = get_16_bit_hex(data[1], data[2])
        real_avg_temp = int((avg_temp / 10) - 40)
        print('real_avg_temp: {}'.format(real_avg_temp))
        self._controller.ext_temp.state = real_avg_temp
        self._controller.send_update()


class ParkingCommand(BaseCommand):
    """
    Custom CAN command
         ID   | byte0 | byte1 | byte2 | byte3 |  byte4  | byte5   |  byte6  |   byte7  |
       0x439  |   RL  |  RLC  |  RRC  |  RR   |    FL   |   FLC   |   FRC   |    FR    |
       """
    def __init__(self):
        super(ParkingCommand, self).__init__()
        self._id = 0x439
        self._f_controller = get_front_parking_controller()
        self._r_controller = get_rear_parking_controller()

    def _execute(self, msg):
        # super(ParkingCommand, self)._execute(msg)
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
        print('Raw data: {}, {}{}{}{}{}{}{}{}\n'.format(msg.data, int(data[0]), int(data[1]), int(data[2]),
                                                      int(data[3]), int(data[4]), int(data[5]), int(data[6]),
                                                      int(data[7])))


class RPMAndSpeedCommand(BaseCommand):
    """
      ID  | byte0  |   byte1   |   byte2   |   byte3    |   byte4  | byte5 | byte6 | byte7 |
    0x460 | ENGINE |   RPM1    |   RPM0    |    SPD1    |   SPD0   |   -   |   -   |   -   |
     byte    |   bit7   |   bit6   |   bit5   |   bit4   |   bit3   |   bit2   |   bit1   |   bit0   |
     ENGINE  |   ONOFF  |          |          |          |          |          |          |          |
    RPM1 + RPM0 = RPM (16 digits)
    SPD1 + SPD0 = Speed (16 digits)
    ENGINE: 0x00 - Engine on
    """
    def __init__(self):
        super(RPMAndSpeedCommand, self).__init__()
        self._id = 0x460

    def _execute(self, msg):
        super(RPMAndSpeedCommand, self)._execute(msg)
        data = msg.data
        rpm = get_16_bit_hex(data[1], data[2])
        speed = get_16_bit_hex(data[3], data[4]) / 10
        print("RPM: {}, speed: {}".format(rpm, speed))


class CoolantTempAndAirPressureCommand(BaseCommand):
    """
      ID  | byte0  |   byte1   |   byte2   |   byte3    |   byte4  | byte5 | byte6 | byte7 |
    0x5c0 |   -    |  COOLANT  |   PRES1   |  PRES0     |     -    |   -   |   -   |   -   |

    COOLANT = Coolant temp - 40 (8 bit)
    PRES1 + PRES0 = Am,bient air pressure (16 bits) [hPa]
    """
    def __init__(self):
        super(CoolantTempAndAirPressureCommand, self).__init__()
        self._id = 0x5c0

    def _execute(self, msg):
        super(CoolantTempAndAirPressureCommand, self)._execute(msg)
        data = msg.data
        coolant = int(data[1]) - 40
        air_pressure = get_16_bit_hex(data[2], data[3])
        print("Coolant: {}, AirPress: {}".format(coolant, air_pressure))


class MileageCommand(BaseCommand):
    """
      ID  | byte0  |   byte1   |   byte2   |   byte3    |   byte4  | byte5 | byte6 | byte7 |
    0x640 |   -    |     -     |   MIL2    |   MIL1     |    MIL   |   -   |   -   |   -   |

    MIL2 + MIL1 + MIL0 = Milage / 100 [km] (24 bit)
    """
    def __init__(self):
        super(MileageCommand, self).__init__()
        self._id = 0x640

    def _execute(self, msg):
        super(MileageCommand, self)._execute(msg)
        data = msg.data
        mileage = get_24_bit_hex(data[2], data[3], data[4]) / 100
        print("mileage: {} km".format(mileage))


class HeadLightsCommand(BaseCommand):
    """
      ID  | byte0  |   byte1   |   byte2   |   byte3    |   byte4  | byte5 | byte6 | byte7 |
    0x3b0 | STATE  |  LIGHT    |     -     |      ?     |     -    |   -   |   -   |   -   |
     byte    |   bit7   |   bit6   |   bit5   |   bit4   |   bit3   |   bit2   |   bit1   |   bit0   |
     STATE  |  CHANGED  |          |          |          |          |          |          |          |
     LIGHT  |     -     |    1     |     1    |     1    |    OFF   |     1    |   PARK   |   DAY    |
       ?    |     -     |          |          |          |          |          |          |          |

    RPM1 + RPM0 = RPM (16 digits)
    SPD1 + SPD0 = Speed (16 digits)
    ENGINE: 0x00 - Engine on
    """
    def __init__(self):
        super(HeadLightsCommand, self).__init__()
        self._id = 0x3b0

    def _execute(self, msg):
        super(HeadLightsCommand, self)._execute(msg)
        data = msg.data
        changed = data[0] >> 7 & 0x01
        if changed:
            ign = data[1] >> 3 & 0x01
            park_mode = data[1] >> 1 & 0x01
            day_mode = data[1] >> 0 & 0x01
            print("ign: {}, park_mode: {}, day_mode: {}".format(ign, park_mode, day_mode))


class PedalsReverseGearCommand(BaseCommand):
    """
      ID  | byte0 | byte1 | byte2 | byte3 | byte4 | byte5 | byte6 | byte7 |
    0x280 | STATE | GEAR  | PEDAL |   -   | CRUISE|   ?   |   -   |   -   |

      byte  |   bit7   |   bit6   |   bit5   |   bit4   |   bit3      |   bit2   |   bit1   |   bit0   |
      STATE | CHANGED  |
      PEDAL |  -      |     -    | KICKDOWN |  BRAKE   | BRAKE/CLUTCH|     -    |  BRAKE   |     -    |
      CRUISE|  -      |     -    |  ACTIVE  |  -       |      -      |     -    |     -    |     -    |
    """
    def __init__(self):
        super(PedalsReverseGearCommand, self).__init__()
        self._id = 0x280
        self._controller = get_door_controller()
        print('PedalsReverseGearCommand init()')

    def _execute(self, msg):
        super(PedalsReverseGearCommand, self)._execute(msg)
        data = msg.data
        changed = data[0] >> 7 & 0x01
        if changed:
            reverse = 1 if data[1] == 0x02 else 0   # 0xff otherwise
            kickdown = data[2] >> 5 & 0x01
            brake = data[2] >> 4 & 0x01
            brake_clutch = data[2] >> 3 & 0x01
            brake2 = data[2] >> 1 & 0x01
            print("kickdown: {}, brake: {}, brake_clutch: {}, brake2: {}, reverse: {}".format(
                kickdown, brake, brake_clutch, brake2, reverse))


class SteeringWheelAndVINCommand(BaseCommand):
    """
      ID  | byte0 | byte1  | byte2  | byte3 | byte4 | byte5 | byte6 | byte7 |
    0x4a0 | STATE | WIPER  | SIGNAL |   -   |  VIN2 | VIN1  | VIN0  |   -   |

      byte  |   bit7   |   bit6   |   bit5   |   bit4   |   bit3   |   bit2   |   bit1   |   bit0   |
      STATE | CHANGED  |
      WIPER |  -      |  DRIZZLE  | NORMAL  |  BACK     |     -    |     -    |    -     |   PARK   |
      SIGNAL|  -      |     -    |    -     |   -       |    -     |   LEFT   |  RIGHT   | REARFOG  |
    """
    def __init__(self):
        super(SteeringWheelAndVINCommand, self).__init__()
        self._id = 0x4a0
        self._controller = get_door_controller()

    def _execute(self, msg):
        super(SteeringWheelAndVINCommand, self)._execute(msg)
        data = msg.data
        changed = data[0] >> 7 & 0x01
        if changed:
            wiper_dizzle = data[1] >> 6 & 0x01
            wiper_normal = data[1] >> 5 & 0x01
            wiper_back = data[1] >> 4 & 0x01
            wiper_park = data[1] >> 0 & 0x01  # Park lights are on
            signal_l = data[2] >> 2 & 0x01
            signal_r = data[2] >> 1 & 0x01
            rear_fog = data[2] >> 0 & 0x01
            print("wiper_dizzle: {}, wiper_normal: {}, wiper_back: {}, wiper_park: {},"
                  " signal_l: {}, signal_r:{}, rear_fog: {}".format(
                wiper_dizzle, wiper_normal, wiper_back, wiper_park, signal_l, signal_r, rear_fog))


class FuelUsageCommand(BaseCommand):
    """
      ID  | byte0  |   byte1   |   byte2   |   byte3    |   byte4  | byte5 | byte6 | byte7 |
    0x630 |  VALID |   FUEL1   |   FUEL0   |  AVGTANK1  | AVGTANK0 | TANK1 | TANK0 |   -   |

    byte  |   bit7   |   bit6   |   bit5   |   bit4   |   bit3   |   bit2   |   bit1   |   bit0   |
    VALID |  -      |     -    |    -     |   -       |    ?     |   ?      | TANKVALID| TANKVALID|


    MIL2 + MIL1 + MIL0 = Milage / 100 [km] (24 bit)
    """
    def __init__(self):
        super(FuelUsageCommand, self).__init__()
        self._id = 0x630

    def _execute(self, msg):
        super(FuelUsageCommand, self)._execute(msg)
        data = msg.data
        not_valid = data[0] >> 0 & 0x01 or data[0] >> 1 & 0x01
        fuel_usage_last_start = get_16_bit_hex(data[1], data[2])  # ml
        fuel_left_in_tank = get_16_bit_hex(data[3], data[4])  # Full = 0x02a0, Empty = 0x0040
        raw_fuel_left_in_tank = get_16_bit_hex(data[5], data[6])

        print("not_valid: {}, fuel_usage_last_start: {}, fuel_left_in_tank: {}, raw_fuel_left_in_tank: {}".format(
            not_valid, fuel_usage_last_start, fuel_left_in_tank, raw_fuel_left_in_tank))


class ACCDiceCommand(BaseCommand):
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
        self._id = 0x530

    def _execute(self, msg):
        super(ACCDiceCommand, self)._execute(msg)
        data = msg.data
        acc_on = data[1] >> 2 & 0x01
        ac_pressure = data[3]  # bar

        print("acc_on: {}, ac_pressure: {}".format(acc_on, ac_pressure))


class ACCCommand(BaseCommand):
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
        self._id = 0x520
        self._climate_controller = get_climate_controller()
        self._temp_controller = get_temp_controller()

    def _execute(self, msg):
        super(ACCCommand, self)._execute(msg)
        data = msg.get('data')
        changed = data[0] >> 7 & 0x01
        if changed:
            rear_heat = data[1] >> 6 & 0x01
            compressor_on = data[1] >> 7 & 0x01
            temp = data[5] - self.INT_TEMP_CONSTANT
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
    CAN_COMMANDS_IDS.ACC: ACCDiceCommand(),
    CAN_COMMANDS_IDS.COOLANT_TEMP_AIR_PRESSURE: CoolantTempAndAirPressureCommand(),
    CAN_COMMANDS_IDS.SID_BEEP_REQUEST: DummyCommand(),
    CAN_COMMANDS_IDS.LIGHT_DIMMER_LIGHT_SENSOR: DummyCommand(),


    CAN_COMMANDS_IDS.MILEAGE: MileageCommand(),
    CAN_COMMANDS_IDS.HEAD_LIGHTS: HeadLightsCommand(),
    CAN_COMMANDS_IDS.PEDALS_REVERSE_GEAR: PedalsReverseGearCommand(),
    CAN_COMMANDS_IDS.STREERING_WHEEL_AND_VIN: SteeringWheelAndVINCommand(),
    CAN_COMMANDS_IDS.FUEL_USAGE: DummyCommand(),
    CAN_COMMANDS_IDS.ENGINE_RPM_AND_SPEED: RPMAndSpeedCommand(),


    CAN_COMMANDS_IDS.STEERING_WHEEL_SID_BUTTONS: DummyCommand(),
    CAN_COMMANDS_IDS.TRIONIC_REPLY_ACK: DummyCommand(),
    CAN_COMMANDS_IDS.TRIONIC_DATA_INIT: DummyCommand(),
    CAN_COMMANDS_IDS.TRIONIC_DATA_QUERY_REPLY: DummyCommand(),
    CAN_COMMANDS_IDS.TRIONIC_DATA_QUERY: DummyCommand(),

    CAN_COMMANDS_IDS.RDS_TIME: DummyCommand(),
    CAN_COMMANDS_IDS.CLOCK: DummyCommand(),
    CAN_COMMANDS_IDS.SECURITY: DummyCommand(),
}
