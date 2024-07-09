import time

from multimedia_controller.constants import CAN_COMMANDS_IDS, CAN_COMMANDS_NAMES
from multimedia_controller.controllers.door_controller import get_door_controller
from multimedia_controller.controllers.climate_controller import get_climate_controller
from multimedia_controller.controllers.parking_controller import (get_front_parking_controller,
                                                                  get_rear_parking_controller)
from multimedia_controller.helpers.utils import get_16_bit_hex, get_24_bit_hex
from multimedia_controller.settings import CAN_DEBOUNCE_TIMEOUT


class BaseCommand:
    def __init__(self):
        self._debounce_time = 0
        self._debounce_timout = CAN_DEBOUNCE_TIMEOUT
        self._controller = None

    def __call__(self, *args, **kwargs):
        if (time.ticks_ms() - self._debounce_time) < self._debounce_timout or not self._validate(*args, **kwargs):
            return
        self._execute(*args, **kwargs)
        self._debounce_time = time.ticks_ms()

    def _validate(self, msg):
        data = msg.get('data')
        id = msg.get('id')
        if id is None or data is None:
            print("[CAN command failed] cannot execute. Missing information ID: {}, data: {}".format(hex(id), data))
            return False
        return True

    def _execute(self, data):
        pass


class DummyCommand(BaseCommand):
    def _execute(self, msg):
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
        self._controller = get_door_controller()
        print('DoorStatusCommand init()')

    def _execute(self, msg):
        data = msg.get('data')
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
        self._controller = get_climate_controller()
        print('ExtTempCommand init()')

    def _execute(self, msg):
        data = msg.get('data')
        avg_temp = get_16_bit_hex(data[1], data[2])
        real_avg_temp = int((avg_temp / 10) - 40)
        print('real_avg_temp: {}'.format(real_avg_temp))
        self._controller.ext_temp.set_state(real_avg_temp)
        self._controller.send_update()


class ParkingCommand(BaseCommand):
    """
         ID   | byte0 | byte1 | byte2 | byte3 |  byte4  | byte5   |  byte6  |   byte7  |
       0x439  |       |       |       |   -   | FL, FLC | FR, FRC | RR, RRC | RL, RLC  |

         byte    |   bit7   |   bit6   |   bit5   |   bit4   |   bit3   |   bit2   |   bit1   |   bit0   |
         FL, FLC |   FLC    |   FLC    |   FLC    |   FLC    |   FL     |   FL     |   FL     |   FL     |
         FR, FRC |   FRC    |   FRC    |   FRC    |   FRC    |   FR     |   FR     |   FR     |   FR     |
         RR, RRC |   RRC    |   RRC    |   RRC    |   RRC    |   RR     |   RR     |   RR     |   RR     |
         RL, RLC |   RLC    |   RLC    |   RLC    |   RLC    |   RL     |   RL     |   RL     |   RL     |
       """
    def __init__(self):
        super(ParkingCommand, self).__init__()
        self._f_controller = get_front_parking_controller()
        self._r_controller = get_rear_parking_controller()
        print('ParkingCommand init()')

    def _unpack_radar_data(self, data):
        """
        Unpacking two radar data from one byte (by 4 bits corresponding).
        Mask: hex(2 ** 4 - 1) = 0x0f
        """
        return data >> 4 & 0x0f, data >> 0 & 0x0f

    def _execute(self, msg):
        data = msg.get('data')
        fl, flc = self._unpack_radar_data(data[4])
        fr, frc = self._unpack_radar_data(data[5])
        self._f_controller.r = fr
        self._f_controller.rc = frc
        self._f_controller.lc = flc
        self._f_controller.l = fl
        self._f_controller.send_update()

        rr, rrc = self._unpack_radar_data(data[6])
        rl, rlc = self._unpack_radar_data(data[7])
        self._r_controller.r = rr
        self._r_controller.rc = rrc
        self._r_controller.lc = rlc
        self._r_controller.l = rl
        self._r_controller.send_update()


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
        self._controller = None
        print('RPMandSpeedCommand init()')

    def _execute(self, msg):
        data = msg.get('data')
        # data = bytearray(data)
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
        self._controller = None
        print('CoolantTempAndAirPressureCommand init()')

    def _execute(self, msg):
        data = msg.get('data')
        # data = bytearray(data)
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
        self._controller = None
        print('MileageCommand init()')

    def _execute(self, msg):
        data = msg.get('data')
        # data = bytearray(data)
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
        self._controller = None
        print('HeadLightsCommand init()')

    def _execute(self, msg):
        data = msg.get('data')
        # data = bytearray(data)
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
        self._controller = get_door_controller()
        print('PedalsReverseGearCommand init()')

    def _execute(self, msg):
        data = msg.get('data')
        changed = data[0] >> 7 & 0x01
        if changed:
            kickdown = data[1] >> 5 & 0x01
            brake = data[1] >> 4 & 0x01
            brake_clutch = data[1] >> 3 & 0x01
            brake2 = data[1] >> 1 & 0x01
            print("kickdown: {}, brake: {}, brake_clutch: {}, brake2: {}".format(kickdown, brake, brake_clutch, brake2))


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
        self._controller = get_door_controller()
        print('SteeringWheelAndVINCommand init()')

    def _execute(self, msg):
        data = msg.get('data')
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
        self._controller = None
        print('FuelUsageCommand init()')

    def _execute(self, msg):
        data = msg.get('data')
        # data = bytearray(data)
        not_valid = data[0] >> 0 & 0x01 or data[0] >> 1 & 0x01
        fuel_usage_last_start = get_16_bit_hex(data[1], data[2])  # ml
        fuel_left_in_tank = get_16_bit_hex(data[3], data[4])  # Full = 0x02a0, Empty = 0x0040
        raw_fuel_left_in_tank = get_16_bit_hex(data[5], data[6])

        print("not_valid: {}, fuel_usage_last_start: {}, fuel_left_in_tank: {}, raw_fuel_left_in_tank: {}".format(
            not_valid, fuel_usage_last_start, fuel_left_in_tank, raw_fuel_left_in_tank))


CANCmdHandlers = {
    CAN_COMMANDS_IDS.DOOR_STATUS: DoorStatusCommand(),
    CAN_COMMANDS_IDS.OUTSIDE_TEMP: ExtTempCommand(),
    CAN_COMMANDS_IDS.SPA_DISTANCE: ParkingCommand(),

    CAN_COMMANDS_IDS.ENGINE_RPM_AND_SPEED: RPMAndSpeedCommand(),
    CAN_COMMANDS_IDS.COOLANT_TEMP_AIR_PRESSURE: CoolantTempAndAirPressureCommand(),
    CAN_COMMANDS_IDS.MILEAGE: MileageCommand(),
    CAN_COMMANDS_IDS.HEAD_LIGHTS: HeadLightsCommand(),
    CAN_COMMANDS_IDS.PEDALS_REVERSE_GEAR: PedalsReverseGearCommand(),
    CAN_COMMANDS_IDS.STREERING_WHEEL_AND_VIN: SteeringWheelAndVINCommand(),
    CAN_COMMANDS_IDS.FUEL_USAGE: DummyCommand(),


    CAN_COMMANDS_IDS.SID_BEEP_REQUEST: DummyCommand(),

    CAN_COMMANDS_IDS.LIGHT_DIMMER_LIGHT_SENSOR: DummyCommand(),

    CAN_COMMANDS_IDS.STEERING_WHEEL_SID_BUTTONS: DummyCommand(),
    CAN_COMMANDS_IDS.TRIONIC_REPLY_ACK: DummyCommand(),
    CAN_COMMANDS_IDS.TRIONIC_DATA_INIT: DummyCommand(),
    CAN_COMMANDS_IDS.TRIONIC_DATA_QUERY_REPLY: DummyCommand(),
    CAN_COMMANDS_IDS.TRIONIC_DATA_QUERY: DummyCommand(),

    CAN_COMMANDS_IDS.RDS_TIME: DummyCommand(),
    CAN_COMMANDS_IDS.CLOCK: DummyCommand(),
    CAN_COMMANDS_IDS.SECURITY: DummyCommand(),
}
