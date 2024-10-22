from machine import Pin, time_pulse_us

from Parking_assistant.settings import (
    PULSE_LEVEL, START_BIT_TIMEOUT, START_BIT_LOW_BOUND, START_BIT_HIGH_BOUND, HIGH_BIT_TIMEOUT,
    HIGH_BIT_LOW_BOUND, HIGH_BIT_HIGH_BOUND
)


def get_packet(pin):
    """
    Packet structure
        1 start bit,
        2 address 1001 XXXX,
        3 value XXXX XXXX,
        4 ending byte 0 (ignor it)
    """
    start_pulse_duration = time_pulse_us(pin, PULSE_LEVEL, START_BIT_TIMEOUT)
    if START_BIT_LOW_BOUND < start_pulse_duration < START_BIT_HIGH_BOUND:
        packet = 0
        for i in range(15, -1, -1):
            bit_pulse_duration = time_pulse_us(pin, PULSE_LEVEL, HIGH_BIT_TIMEOUT)
            if HIGH_BIT_LOW_BOUND < bit_pulse_duration < HIGH_BIT_HIGH_BOUND:
                packet |= 1 << i
        addr = (packet >> 8) & 0b00001111  # first 4 bytes are not interested, 1001 always the same
        value = packet & 0b11111111


pin = Pin(16, Pin.IN, Pin.PULL_DOWN)
