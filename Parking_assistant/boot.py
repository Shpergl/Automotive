from machine import Pin


def init_CAN():
    from AC_controller.can.can_bus import get_CAN_bus
    global can
    can = get_CAN_bus()

can = None

init_CAN()

def handle_front_enable_interrupt(pin):



def handle_rear_enable_interrupt(pin):



def init():
    front_enable_pin = Pin(15, Pin.IN)
    front_enable_pin.irq(trigger=Pin.IRQ_RAISING, handler=handle_front_enable_interrupt)
    front_enable_pin = Pin(15, Pin.OUT)

    rear_enable_pin = Pin(15, Pin.IN)
    rear_enable_pin.irq(trigger=Pin.IRQ_RAISING, handler=handle_rear_enable_interrupt)
    rear_enable_pin = Pin(15, Pin.OUT)

    # can_interrupt_pin = Pin(16, Pin.IN, Pin.PULL_UP)
    # can_interrupt_pin.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=can.handle_can_cmd)


def start():
