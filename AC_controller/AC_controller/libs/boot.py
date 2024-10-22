from machine import I2C, Pin, PWM, Timer
from ads1x15 import ADS1115



vcc_relay = Pin(6, Pin.OUT, Pin.PULL_DOWN)
led = Pin(25, Pin.OUT)

i2c_bus = I2C(1, scl=Pin(27), sda=Pin(26))
#devices = i2c_bus.scan()
adc = ADS1115(i2c_bus, address=72, gain=0)


def shutdown(timer):
    global SD_timer
    global is_shutting_down
    vcc_relay.value(0)
    led.value(0)
    SD_timer.deinit()
    is_shutting_down = False


SD_timer = Timer()
is_shutting_down = False
def handle_power_interrupt(pin):
    global is_shutting_down
    global SD_timer
    if pin.value() == 1 and not is_shutting_down:
        is_shutting_down = True
        vcc_relay.value(1)
        led.value(1)
        SD_timer.init(period=2000, mode=Timer.ONE_SHOT, callback=shutdown)


acc_in_pin = Pin(5, Pin.IN, Pin.PULL_UP)
acc_in_pin.irq(trigger=Pin.IRQ_RISING | Pin.IRQ_FALLING, handler=handle_power_interrupt)


def measure_voltage():
    value1 = adc.read(0, 0)
    value2 = adc.read(0, 1)
    value3 = adc.read(1, 0)

    v1 = adc.raw_to_v(value1)
    v2 = adc.raw_to_v(value2)
    v3 = adc.raw_to_v(value3)

    print("V1={}, V2={}, V3={}".format(v1, v2, v3))
    print("Voltage1: {}".format(v2))
    print("Voltage2: {}".format(v1*3.4))


def handle_timer(_):
    measure_voltage()

V_timer = Timer(period=10000, mode=Timer.PERIODIC, callback=handle_timer)


ac_compressor_relay = Pin(16, Pin.OUT, Pin.PULL_DOWN)
rear_window_heat_relay = Pin(17, Pin.OUT, Pin.PULL_DOWN)
heat_relay = Pin(18, Pin.OUT, Pin.PULL_DOWN)
cycle_air_relay = Pin(19, Pin.OUT, Pin.PULL_DOWN)

AC_fan = PWM(Pin(20))
AC_fan.freq(20000)









