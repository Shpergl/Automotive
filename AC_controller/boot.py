from machine import Pin

from multimedia_controller import settings
from multimedia_controller.constants import UART_TYPES


def init_UART():
    from multimedia_controller.uart.uart_bus import get_UART_bus
    uart = get_UART_bus()
    Pin(settings.UART.RX_PIN).irq(handler=uart.handle_uart_cmd, trigger=Pin.IRQ_FALLING)


def init_CAN():
    from multimedia_controller.can.can_bus import get_CAN_bus
    global can
    can = get_CAN_bus()


def init_devices():
    from multimedia_controller.devices.relays import (ACCompressorRelay, ACCompressorFanRelay, ACCycleRelay,
                                                      ACRearWindowHeatRelay, ACCoolantRelay)
    from multimedia_controller.devices.pwm_devices import (FanDirTemp, FanDirWindow, FanDirDownMiddle, SeatHeatL,
                                                           SeatHeatR, ACFan)
    from multimedia_controller.devices.sid_text import SIDTextDevice
    from multimedia_controller.devices.sensors import TempSensors

    ACCompressorRelay()
    ACCompressorFanRelay()
    ACCycleRelay()
    ACCoolantRelay()
    ACRearWindowHeatRelay()
    ACFan()
    FanDirTemp()
    FanDirWindow()
    FanDirDownMiddle()
    SeatHeatL()
    SeatHeatR()
    TempSensors()
    SIDTextDevice()

# TODO Check additional behaviour
def send_illum_status(uart, status):
    # VIM_MCU_HEAD_LIGHT_STATUS_PROPERTY
    #status = 1 # or 0
    data = [0x00]
    data[0] |= status << 7  # VIM_MCU_HEAD_LIGHT_STATUS_PROPERTY
    uart._send(UART_TYPES.CH_CMD_ILL_INFO, data)


def sendSpeed(uart, speed):
    # "%.1f",(param[0]*256+param[1])/16.0)
    s1, s2 = speed
    data = [0x00, 0x00]
    data[0] = s1  # VIM_SPEEDO_METER_PROPERTY
    data[1] = s2  # VIM_SPEEDO_METER_PROPERTY
    uart._send(UART_TYPES.CH_CMD_VEHICLE_SPPED_SIGNAL, data)


def sendRearRadar(uart):
    # CH_CMD_REAR_RADAR_INFO = 0x22
    import time
    for i in range(0, 10):
        data = [0x00, 0x00, 0x00, 0x00]
        p1, p2, p3, p4 = [i, i, i, i]
        data[0] = p1  # [0, 1, 2, 4, 6, 8]
        data[1] = p2  # [0, 1, 2, 4, 6, 8, 9]
        data[2] = p3  # [0, 1, 2, 4, 6, 8, 9]
        data[3] = p4  # [0, 1, 2, 4, 6, 8]
        uart._send(0x22, data)
        print("distance {}".format(i))
        time.sleep(1)


def sendParkingOn(uart, status):
    # CH_CMD_PARKING_RADAR_SWITCH_INFO = 0x07
    data = [0x00]
    data[0] |= status << 0  # VIM_VEHICLE_RADAR_SWITCH_PROPERTY
    uart._send(0x07, data)


can = None

init_UART()
init_CAN()
init_devices()


def handle_power_interrupt(pin):
    print("Переривання! +5В відсутнє.")
    #with open('/state.txt', 'w') as f:
    #    f.write('ON')


#power_supply_pin = Pin(15, Pin.IN)
#power_supply_pin.irq(trigger=Pin.IRQ_FALLING, handler=handle_power_interrupt)

#can_interrupt_pin = Pin(16, Pin.IN, Pin.PULL_UP)
#can_interrupt_pin.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=can.handle_can_cmd)

print("Inited")


# See reference of HU code
# https://github.com/runmousefly/Work/blob/master/MctCoreServices/src/com/mct/carmodels/RZC_GMSeriesProtocol.java#L55

# box -> HA start commands
# [0x2e, 0x30, 0x10, 0x42, 0x49, 0x4e, 0x41, 0x52, 0x59, 0x20, 0x42, 0x4b, 0x20, 0x56, 0x32, 0x32, 0x38, 0x00, 0x00, 0x3b] CH_CMD_PROTOCOL_VERSION_INFO
# [0x2e, 0xee, 0x02, 0xff, 0xff, 0x11] ?
# [0x2e, 0x24, 0x02, 0x00, 0x00, 0xd9] CH_CMD_BASE_INFO
# [0x2e, 0x05, 0x02, 0x00, 0x00, 0xf8] CH_CMD_AIR_CONDITON_CONTROL_INFO
# [0x2e, 0x06, 0x02, 0x00, 0x00 0xf7] CH_CMD_VEHICLE_SETTING_INFO
# [0x2e, 0x0a, 0x03, 0x00, 0x00, 0x00, 0xf2] CH_CMD_VEHICLE_SETTING_INFO2
# [0x2e, 0x63, 0x06, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x96] ?

# HA-> box
# [2e, 81, 01, 01, 7c] CANBOX_CMD_REQ_START
