from machine import Pin, Timer, I2C
import onewire, ds18x20

import settings
from libs.ads1x15 import ADS1115
from constants import UART_TYPES, AC_STATUS, SUN_SENSOR_STATUS, AC_COOL_MODE_AUTO
from controllers.climate_controller import get_climate_controller, get_temp_controller
from helpers.observer import Observer
from helpers.utils import round_float


class OneWireTempSensor:
    def __init__(self, name, pin):
        self._name = name
        self._pin = pin
        self._sensors = {}
        self._temp_states = {}
        self._ow = None
        self._ds = None
        self.init()

    def init(self):
        self._ow = onewire.OneWire(Pin(self._pin))
        self._ds = ds18x20.DS18X20(self._ow)
        self._add_sensors()
        self._temp_states = {k: 0 for k in settings.ONE_WIRE_TEMP_SENSORS.keys()}

    def _add_sensors(self):
        scanned_sensors = self._ds.scan()
        if not scanned_sensors:
            print("Cannot find any temperature sensor")  # TODO send error to UART/CAN
            return
        print("Temperature sensors found: {}".format(scanned_sensors))
        for sensor_id in settings.ONE_WIRE_TEMP_SENSORS.values():
            if sensor_id not in scanned_sensors:
                print("Cannot find sensor: {}".format(sensor_id))  # TODO send error to UART/CAN
                continue
            sensor_name = settings.ONE_WIRE_TEMP_SENSORS_ID_TO_NAME[sensor_id]
            self._sensors[sensor_name] = sensor_id

    def measure(self):
        if not self._sensors:
            return
        self._ds.convert_temp()
        for sensor_name, sensor_id in self._sensors.items():
            self._temp_states[sensor_name] = round_float(self._ds.read_temp(sensor_id))
        return self._temp_states


class TempSensors(Observer):
    def __init__(self):
        self._sensors = OneWireTempSensor('OneWireTempSensors', settings.PINS.ONE_WIRE_TEMP_SENSORS_PIN)
        self.subscribe(get_climate_controller())
        self._climate_controller = get_climate_controller()
        self._temp_controller = get_temp_controller()
        self._timer = Timer()
        self._measured_temps = {}

    def _update_sensors(self, _):
        new_temps = self._sensors.measure()
        if self._measured_temps.values() == new_temps.values():
            return
        self._measured_temps = new_temps
        print("Temperature was updated: {}".format(self._measured_temps))
        for name, temp in self._measured_temps.items():
            self._temp_controller.set_temp(name, temp)
        self._temp_controller.send_update()

    def update(self, subject_type, subject):
        if subject_type == UART_TYPES.AC:
            if subject.ac_status == AC_STATUS.ON:
                self._timer.init(mode=Timer.PERIODIC,
                                 callback=self._update_sensors,
                                 period=settings.ONE_WIRE_MEASURE_PERIOD)
            else:
                self._timer.deinit()


class ADCSensors:
    ADC_ADDRESS = 72
    ADC_GAIN = 0
    ADC_VOLTAGE_CONVERSION_CONSTANT = 3.4
    ACC_VOLTAGE_INDEX = 3

    def __init__(self):
        self._i2c_bus = I2C(settings.I2C.ID, scl=Pin(settings.PINS.ADC_SCL), sda=Pin(settings.PINS.ADC_SDA))
        self._adc = ADS1115(self._i2c_bus, address=self.ADC_ADDRESS, gain=self.ADC_GAIN)
        self._measured_values = {}
        self._timer = Timer()
        self._timer.init(mode=Timer.PERIODIC,
                         callback=self._measure,
                         period=settings.ADC_MEASURING_PERIOD)
        self._climate_controller = get_climate_controller()

    @property
    def acc_voltage(self):
        return self._measured_values.get(self.ACC_VOLTAGE_INDEX, 0) * self.ADC_VOLTAGE_CONVERSION_CONSTANT

    def _measure(self, _):
        for i in range(4):
            self._measured_values[i] = self._adc.raw_to_v(self._adc.read(channel1=i))
        self._climate_controller.acc_voltage = self.acc_voltage
        self._climate_controller.send_update()


class SunSensor(Observer):
    def __init__(self):
        self._pin = Pin(settings.PINS.SUN_SENSOR_PIN)
        self._sun_state = SUN_SENSOR_STATUS.OFF
        self._pin.irq(trigger=Pin.IRQ_FALLING, handler=self._handle_sensor_update)
        self._climate_controller = get_climate_controller()

    def _handle_sensor_update(self, pin):
        self._sun_state = SUN_SENSOR_STATUS.ON if pin == 1 else SUN_SENSOR_STATUS.OFF
        if self._climate_controller.auto == AC_COOL_MODE_AUTO.ON:
            self._climate_controller.sun_sensor = self._sun_state
            self._climate_controller.send_update()
