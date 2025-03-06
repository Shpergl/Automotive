from machine import Pin, PWM

import settings
from helpers.observer import Observer
from helpers.utils import scale, convert_gui_temp, get_corrected_temp
from constants import UART_TYPES, AC_FAN_DIR, FAN_DIR_SERVO_POSITION, CONTROLLER_TYPES, AC_STATUS, AC_COOL_MODE_AUTO
from controllers.climate_controller import get_climate_controller, get_temp_controller


"""
Init all devices in boot.py -> init_devices()
"""


class BasePWM:
    def __init__(self):
        self._motor = None
        self._name = None
        self._pin = None
        self._current_duty = None
        self._pwm_freq = settings.SERVO_PWM_FREQ

    def init(self):
        self._motor = PWM(Pin(self._pin))
        self._motor.freq(self._pwm_freq)

    @property
    def state(self):
        return self._current_duty

    @state.setter
    def state(self, duty):
        if self._current_duty != duty:
            self._current_duty = duty
            self._motor.duty_u16(self._current_duty)


class BaseDutyRangePWM(BasePWM):
    def __init__(self):
        super(BaseDutyRangePWM, self).__init__()
        self._duty_range = None

    @property
    def duty_range(self):
        return self._duty_range


class TemperatureServo(BaseDutyRangePWM):
    def __init__(self):
        super(TemperatureServo, self).__init__()
        self._name = 'TemperatureServo'
        self._pin = settings.PINS.AC_TEMP_SERVO
        self._duty_range = settings.AC_TEMP_DUTIES_RANGE
        self.init()


class FanDirTemp(Observer):
    """
    switch between cold and heated air
    """
    def __init__(self):
        self._desired_l_temp = None
        self._desired_r_temp = None
        # self._ac_status = None
        # self._current_temp = None
        self._servo = TemperatureServo()
        self.subscribe(get_climate_controller())
        self.subscribe(get_temp_controller())

    # def _get_corrected_temp(self, sensors_state):
        # mixed_temp = sensors_state[settings.TEMP_SENSORS.MIXED] - 20

        # if self._current_temp is None:
        #     self._current_temp = mixed_temp

        # temp_delta = abs(self._desired_l_temp - mixed_temp)
        # if self._desired_l_temp > mixed_temp:
        #     self._current_temp = max(self._current_temp - temp_delta, min(settings.AC_TEMP_RANGE))
        # elif self._desired_l_temp < mixed_temp:
        #     self._current_temp = min(self._current_temp + temp_delta, max(settings.AC_TEMP_RANGE))
        # return self._current_temp

    def update(self, subject_type, subject):
        if subject_type == UART_TYPES.AC:
            print('Converted: {}'.format(convert_gui_temp(subject.l_temp.state)))
            self._desired_l_temp = convert_gui_temp(subject.l_temp.state)
            self._desired_r_temp = convert_gui_temp(subject.r_temp.state)
            # self._ac_status = subject.ac_status
        if subject_type == CONTROLLER_TYPES.TEMP:
            # if self._ac_status == AC_STATUS.OFF:
            #     self._current_temp = None
            #     return
            mixed_temp = subject.sensors_state.get(settings.TEMP_SENSORS.MIXED)

            if mixed_temp:
                corrected_temp = get_corrected_temp(self._desired_l_temp, mixed_temp)
                print('current_state: {}'.format(corrected_temp))
                duty = scale(settings.AC_TEMP_RANGE, self._servo.duty_range, corrected_temp)
                print("duty: {}".format(duty))
                self._servo.state = duty


class FanDirWindowServo(BasePWM):
    def __init__(self):
        super(FanDirWindowServo, self).__init__()
        self._name = 'FanDirWindowServo'
        self._pin = settings.PINS.FAN_DIR_WINDOW_SERVO
        self.init()


class FanDirWindow(Observer):
    """
    switch air between window and other directions
    """
    def __init__(self):
        self._servo = FanDirWindowServo()
        self.subscribe(get_climate_controller())

    def update(self, subject_type, subject):
        if subject_type == UART_TYPES.AC:
            if subject.fan_dir in (AC_FAN_DIR.AC_FAN_DIR_UP, AC_FAN_DIR.AC_FAN_DIR_FRONT_WINDOW):
                self._servo.state = settings.FAN_DIR_WINDOW_DUTIES[FAN_DIR_SERVO_POSITION.RIGHT]
            elif subject.fan_dir in (AC_FAN_DIR.AC_FAN_DIR_UP_AND_DOWN, AC_FAN_DIR.AC_FAN_DIR_UP_DOWN_CENTER):
                self._servo.state = settings.FAN_DIR_WINDOW_DUTIES[FAN_DIR_SERVO_POSITION.MIDDLE]
            else:
                self._servo.state = settings.FAN_DIR_WINDOW_DUTIES[FAN_DIR_SERVO_POSITION.LEFT]


class FanDirDownMiddleServo(BasePWM):
    def __init__(self):
        super(FanDirDownMiddleServo, self).__init__()
        self._name = 'FanDirDownMiddleServo'
        self._pin = settings.PINS.FAN_DIR_DOWN_MIDDLE_SERVO
        self.init()


class FanDirDownMiddle(Observer):
    """
    switch air between down and middle
    """
    def __init__(self):
        self._servo = FanDirDownMiddleServo()
        self.subscribe(get_climate_controller())

    def update(self, subject_type, subject):
        if subject_type == UART_TYPES.AC:
            if subject.fan_dir in (AC_FAN_DIR.AC_FAN_DIR_CENTER, AC_FAN_DIR.AC_FAN_DIR_CENTER_AND_UP):
                self._servo.state = settings.FAN_DIR_DOWN_MIDDLE_DUTIES[FAN_DIR_SERVO_POSITION.RIGHT]
            elif subject.fan_dir in (AC_FAN_DIR.AC_FAN_DIR_DOWN_AND_CENTER, AC_FAN_DIR.AC_FAN_DIR_UP_DOWN_CENTER):
                self._servo.state = settings.FAN_DIR_DOWN_MIDDLE_DUTIES[FAN_DIR_SERVO_POSITION.MIDDLE]
            elif subject.fan_dir == AC_FAN_DIR.AC_FAN_DIR_DOWN:
                self._servo.state = settings.FAN_DIR_DOWN_MIDDLE_DUTIES[FAN_DIR_SERVO_POSITION.LEFT]


class SeatHeatLPWM(BaseDutyRangePWM):
    def __init__(self):
        super(SeatHeatLPWM, self).__init__()
        self._name = 'SeatHeatLPWM'
        self._pin = settings.PINS.SEAT_HEAT_L
        self._duty_range = settings.SEAT_HEAT_DUTIES_RANGE
        self._pwm_freq = settings.SEAT_HEAT_PWM_FREQ
        self.init()
        self.state = min(settings.SEAT_HEAT_DUTIES_RANGE)


class SeatHeatL(Observer):
    def __init__(self):
        self._heater = SeatHeatLPWM()
        self.subscribe(get_climate_controller())

    def update(self, subject_type, subject):
        if subject_type == UART_TYPES.AC:
            self._heater.state = scale(settings.SEAT_HEAT_RANGE, self._heater.duty_range, subject.l_seat_heat.state)


class SeatHeatRPWM(BaseDutyRangePWM):
    def __init__(self):
        super(SeatHeatRPWM, self).__init__()
        self._name = 'SeatHeatRPWM'
        self._pin = settings.PINS.SEAT_HEAT_R
        self._duty_range = settings.SEAT_HEAT_DUTIES_RANGE
        self._pwm_freq = settings.SEAT_HEAT_PWM_FREQ
        self.init()
        self.state = min(settings.SEAT_HEAT_DUTIES_RANGE)


class SeatHeatR(Observer):
    def __init__(self):
        self._heater = SeatHeatRPWM()
        self.subscribe(get_climate_controller())

    def update(self, subject_type, subject):
        if subject_type == UART_TYPES.AC:
            self._heater.state = scale(settings.SEAT_HEAT_RANGE, self._heater.duty_range, subject.r_seat_heat.state)


class ACFanPWM(BaseDutyRangePWM):
    def __init__(self):
        super(ACFanPWM, self).__init__()
        self._name = 'ACFanPWM'
        self._pin = settings.PINS.AC_FAN
        self._pwm_freq = settings.FAN_PWM_FREQ
        self._duty_range = settings.FAN_SPEED_DUTIES_RANGE
        self.init()
        self.state = min(settings.FAN_SPEED_RANGE)


class ACFan(Observer):
    def __init__(self):
        self._fan = ACFanPWM()
        self._ac_auto_mode = None
        self.subscribe(get_climate_controller())

    def update(self, subject_type, subject):
        if subject_type == UART_TYPES.AC:
            self._fan.state = self._fan.duty_range[subject.fan_speed.state]
            self._ac_auto_mode = subject.auto

        if subject_type == CONTROLLER_TYPES.TEMP:
            if self._ac_auto_mode == AC_COOL_MODE_AUTO.ON:
                corrected_temp = get_corrected_temp(subject.sensors_state[settings.TEMP_SENSORS.MIXED],
                                                    subject.sensors_state[settings.TEMP_SENSORS.INT])
                print('ACFan corrected temp: {}'.format(corrected_temp))
                duty = scale(settings.AC_TEMP_RANGE, self._fan.duty_range, corrected_temp)
                print("ACFan duty: {}".format(duty))
                self._fan.state = duty
                # TODO maybe send update to controller to show new fan state on gui
