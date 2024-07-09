from machine import Pin, Timer
import onewire, ds18x20

from multimedia_controller import settings
from multimedia_controller.constants import UART_TYPES, AC_STATUS
from multimedia_controller.controllers.climate_controller import get_climate_controller, get_temp_controller
from multimedia_controller.helpers.observer import Observer
from multimedia_controller.helpers.utils import round_float


class OneWireTempSensor:
    def __init__(self, name, pin):
        self._name = name
        self._pin = pin
        self._sensors_ids = settings.ONE_WIRE_TEMP_SENSORS.values()
        self._temp_states = {}
        self._ow = None
        self._ds = None
        self._timer = Timer()
        self.init()

    def init(self):
        self._ow = onewire.OneWire(Pin(self._pin))
        self._ds = ds18x20.DS18X20(self._ow)
        self._check_sensors()
        self._temp_states = {k: 0 for k in settings.ONE_WIRE_TEMP_SENSORS.keys()}

    def _check_sensors(self):
        for sensor in self._ds.scan():
            if sensor not in self._sensors_ids:
                print("Cannot find sensor: {}".format(sensor))  # TODO send error to UART/CAN
                return False
        return True

    def measure(self):
        self._ds.convert_temp()
        for sensor_name, sensor_id in settings.ONE_WIRE_TEMP_SENSORS.items():
            self._temp_states[sensor_name] = round_float(self._ds.read_temp(sensor_id))
        return self._temp_states


class TempSensors(Observer):
    def __init__(self):
        self._sensors = OneWireTempSensor('OneWireTempSensors', settings.PINS.ONE_WIRE_TEMP_SENSORS)
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

