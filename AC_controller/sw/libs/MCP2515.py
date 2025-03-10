
from collections import namedtuple
from struct import unpack_from, pack_into
from time import sleep, sleep_ms
from micropython import const
from machine import SPI, Pin
from libs.myTimer import Timer
from libs.canio import *


# modes
_MODE_NORMAL = const(0x00)
_MODE_SLEEP = const(0x20)
_MODE_LOOPBACK = const(0x40)
_MODE_LISTENONLY = const(0x60)
_MODE_CONFIG = const(0x80)

# commands
_RESET = const(0xC0)
_WRITE = const(0x02)
_READ = const(0x03)
_BITMOD = const(0x05)

_LOAD_TX0 = const(0x40)
_LOAD_TX1 = const(0x42)
_LOAD_TX2 = const(0x44)

_READ_STATUS = const(0xA0)

_SEND_TX0 = const(0x81)
_SEND_TX1 = const(0x82)
_SEND_TX2 = const(0x84)
_SEND_ALL = const(0x87)

_READ_RX0 = const(0x90)
_READ_RX1 = const(0x94)

# Registers
_CANINTE = const(0x2B)
_CANINTF = const(0x2C)
_CANSTAT = const(0x0E)
_CANCTRL = const(0x0F)

_CNF3 = const(0x28)
_CNF2 = const(0x29)
_CNF1 = const(0x2A)

_TXB0CTRL = const(0x30)
_TXB0SIDH = const(0x31)

_TXB1CTRL = const(0x40)
_TXB1SIDH = const(0x41)

_TXB2CTRL = const(0x50)
_TXB2SIDH = const(0x51)

_RXB0CTRL = const(0x60)
_RXB0SIDH = const(0x61)

_RXB1CTRL = const(0x70)
_RXB1SIDH = const(0x71)

_TX0IF = const(0x04)
_TX1IF = const(0x08)
_TX2IF = const(0x10)

# Filters & Masks
_RXM0SIDH = const(0x20)
_RXM1SIDH = const(0x24)
MASKS = [_RXM0SIDH, _RXM1SIDH]

_RXF0SIDH = const(0x00)
_RXF1SIDH = const(0x04)
_RXF2SIDH = const(0x08)
_RXF3SIDH = const(0x10)
_RXF4SIDH = const(0x14)
_RXF5SIDH = const(0x18)
FILTERS = [[_RXF0SIDH, _RXF1SIDH], [_RXF2SIDH, _RXF3SIDH, _RXF4SIDH, _RXF5SIDH]]
# bits/flags
_RX0IF = const(0x01)
_RX1IF = const(0x02)
_WAKIF = const(0x40)
# _MERRF = const(0x80)

# Standard/Extended ID Buffers, Masks, Flags
_TXB_EXIDE_M_16 = const(0x08)
_TXB_TXREQ_M = const(0x08)  # TX request/completion bit

EXTID_TOP_11_WRITE_MASK = 0x1FFC0000
EXTID_TOP_11_READ_MASK = 0xFFE00000

EXTID_BOTTOM_29_MASK = (1 << 29) - 1  # bottom 18 bits
EXTID_BOTTOM_18_MASK = (1 << 18) - 1  # bottom 18 bits
STDID_BOTTOM_11_MASK = 0x7FF

EXTID_FLAG_MASK = (
    1 << 19
)  # to set/get the "is an extended id?" flag from a 4-byte ID buffer

# masks
_MODE_MASK = const(0xE0)

_RXB_RX_MASK = const(0x60)
_RXB_BUKT_MASK = const((1 << 2))
_RXB_RX_STDEXT = const(0x00)

_STAT_RXIF_MASK = const(0x03)
_RTR_MASK = const(0x40)

_STAT_TXIF_MASK = const(0xA8)
_STAT_TX0_PENDING = const(0x04)
_STAT_TX1_PENDING = const(0x10)
_STAT_TX2_PENDING = const(0x40)

_STAT_TX_PENDING_MASK = const(_STAT_TX0_PENDING | _STAT_TX1_PENDING | _STAT_TX2_PENDING)

###### Bus State and Error Counts ##########

# TEC: TRANSMIT ERROR COUNTER REGISTER (ADDRESS: 1Ch)
_TEC = const(0x1C)
_REC = const(0x1D)
# REC: RECEIVE ERROR COUNTER REGISTER (ADDRESS: 1Dh)
_EFLG = const(0x2D)

############ Misc Consts #########
_SEND_TIMEOUT_MS = const(5)  # 500ms
_MAX_CAN_MSG_LEN = 8  # ?!
# perhaps this will be stateful later?
TransmitBuffer = namedtuple(
    "TransmitBuffer",
    ["CTRL_REG", "STD_ID_REG", "INT_FLAG_MASK", "LOAD_CMD", "SEND_CMD"],
)

# perhaps this will be stateful later? #TODO : dedup with above
ReceiveBuffer = namedtuple(
    "TransmitBuffer",
    ["CTRL_REG", "STD_ID_REG", "INT_FLAG_MASK", "LOAD_CMD", "SEND_CMD"],
)

# This is magic, don't disturb the dragon
# expects a 16Mhz crystal
_BAUD_RATES = {
    # CNF1, CNF2, CNF3
    1000000: (0x00, 0xD0, 0x82),
    500000: (0x00, 0x91, 0x01),
    # 500000: (0x00, 0xF0, 0x86),
    250000: (0x41, 0xF1, 0x85),
    200000: (0x01, 0xFA, 0x87),
    125000: (0x03, 0xF0, 0x86),
    100000: (0x03, 0xFA, 0x87),
    95000: (0x03, 0xAD, 0x07),
    83300: (0x03, 0xBE, 0x07),
    80000: (0x03, 0xFF, 0x87),
    50000: (0x07, 0xFA, 0x87),
    40000: (0x07, 0xFF, 0x87),
    33000: (0x09, 0xBE, 0x07),
    31250: (0x0F, 0xF1, 0x85),
    25000: (0x0F, 0xBA, 0x07),
    20000: (0x0F, 0xFF, 0x87),
    10000: (0x1F, 0xFF, 0x87),
    5000: (0x3F, 0xFF, 0x87),
    666000: (0x00, 0xA0, 0x04),
    47619: (0x06, 0x9b, 0x02)
}



class MCP2515:
    """MCP2515"""

    def __init__(self, spi_id, baud, sck, mosi, miso, cs, baudrate, loopback: bool = False,
                 silent: bool = False, debug: bool = False):
        """A common shared-bus protocol.

        :param int spiBlock: The SPI bus used to communicate with the MCP2515
        :param int csPin:  SPI bus enable pin
        :param int baudrate: The bit rate of the bus in Hz, using a 16Mhz crystal. All devices on\
            the bus must agree on this value. Defaults to 250000.
        :param bool loopback: Receive only packets sent from this device, and send only to this\
        device. Requires that `silent` is also set to `True`, but only prevents transmission to\
        other devices. Otherwise the send/receive behavior is normal.
        :param bool silent: When `True` the controller does not transmit and all messages are\
        received, ignoring errors and filters. This mode can be used to “sniff” a CAN bus without\
        interfering. Defaults to `False`.
        :param bool auto_restart: **Not supported by hardware. An `AttributeError` will be raised\
        if `auto_restart` is set to `True`** If `True`, will restart communications after entering\
        bus-off state. Defaults to `False`.

        :param bool debug: If `True`, will enable printing debug information. Defaults to `False`.
        """

        if loopback and not silent:
            raise AttributeError("Loopback mode requires silent to be set")
        
        self._debug = debug

        self.spi = SPI(spi_id, baud, sck=Pin(sck), mosi=Pin(mosi), miso=Pin(miso))
        self.spi.init()
        
        self.cs = Pin(cs, Pin.OUT)
        self.cs.on()

        self._buffer = bytearray(20)
        self._id_buffer = bytearray(4)
        self._unread_message_queue = []
        self._timer = Timer()
        self._tx_buffers = []
        self._rx0_overflow = False
        self._rx1_overflow = False
        self._masks_in_use = []
        self._filters_in_use = [[], []]
        self._mode = None
        self._bus_state = BusState.ERROR_ACTIVE
        self._baudrate = baudrate
        self._loopback = loopback
        self._silent = silent
        self._baudrate = baudrate

        self._init_buffers()
        self.initialize()

    def _init_buffers(self):

        self._tx_buffers = [
            TransmitBuffer(
                CTRL_REG=_TXB0CTRL,
                STD_ID_REG=_TXB0SIDH,
                INT_FLAG_MASK=_TX0IF,
                LOAD_CMD=_LOAD_TX0,
                SEND_CMD=_SEND_TX0,
            ),
            TransmitBuffer(
                CTRL_REG=_TXB1CTRL,
                STD_ID_REG=_TXB1SIDH,
                INT_FLAG_MASK=_TX1IF,
                LOAD_CMD=_LOAD_TX1,
                SEND_CMD=_SEND_TX1,
            ),
            TransmitBuffer(
                CTRL_REG=_TXB2CTRL,
                STD_ID_REG=_TXB2SIDH,
                INT_FLAG_MASK=_TX2IF,
                LOAD_CMD=_LOAD_TX2,
                SEND_CMD=_SEND_TX2,
            ),
        ]

    def initialize(self):
        """Return the sensor to the default configuration"""
        self._reset()
        # our mode set skips checking for sleep
        self._set_mode(_MODE_CONFIG)

        self._set_baud_rate()

        # intialize TX and RX registers
        for idx in range(14):
            self._set_register(_TXB0CTRL + idx, 0)
            self._set_register(_TXB1CTRL + idx, 0)
            self._set_register(_TXB2CTRL + idx, 0)

        self._set_register(_RXB0CTRL, 0)
        self._set_register(_RXB1CTRL, 0)
        # # # interrupt mode
        # TODO: WHAT IS THIS
        self._set_register(_CANINTE, _RX0IF | _RX1IF)

        sleep(0.010)

        self._mod_register(
            _RXB0CTRL,
            _RXB_RX_MASK | _RXB_BUKT_MASK,
            _RXB_RX_STDEXT | _RXB_BUKT_MASK,
        )

        self._mod_register(_RXB1CTRL, _RXB_RX_MASK, _RXB_RX_STDEXT)
        if self.loopback:
            new_mode = _MODE_LOOPBACK
        elif self.silent:
            new_mode = _MODE_LISTENONLY
        else:
            new_mode = _MODE_NORMAL

        self._set_mode(new_mode)

    def send(self, message_obj):
        """Send a message on the bus with the given data and id. If the message could not be sent
         due to a full fifo or a bus error condition, RuntimeError is raised.

        Args:
            message (canio.Message): The message to send. Must be a valid `canio.Message`
        """

        tx_buff = self._get_tx_buffer()  # info = addr.
        if tx_buff is None:
            print("No transmit buffer available to send")
            return False

        #print("\t\tTX Buffer:", tx_buff)

        return self._write_message(tx_buff, message_obj)

    @property
    def unread_message_count(self):
        """The number of messages that have been received but not read with `read_message`

        Returns:
            int: The unread message count
        """
        self._read_from_rx_buffers()

        return len(self._unread_message_queue)

    def read_message(self):
        """Read the next available message

        Returns:
            `canio.Message`: The next available message or None if one is not available
        """
        if self.unread_message_count == 0:
            return None

        return self._unread_message_queue.pop(0)

    def _read_rx_buffer(self, read_command):
        for i in range(len(self._buffer)):
            self._buffer[i] = 0

        # read from buffer
        tmp = bytearray(1)
        self.cs.off() 
        self.spi.write_readinto(bytes([read_command]), tmp)
        self._buffer = bytearray(self.spi.read(15))
        self.cs.on() 

        ######### Unpack IDs/ set Extended #######
        raw_ids = unpack_from(">I", self._buffer)[0]
        extended, sender_id = self._unload_ids(raw_ids)
        ############# Length/RTR Size #########
        dlc = self._buffer[4]
        # length is max 8
        message_length = min(8, dlc & 0xF)

        if (dlc & _RTR_MASK) > 0:
            frame_obj = RemoteTransmissionRequest(
                sender_id, message_length, extended=extended
            )
        else:
            frame_obj = Message(
                sender_id,
                data=bytes(self._buffer[5 : 5 + message_length]),
                extended=extended,
            )
        self._unread_message_queue.append(frame_obj)

    def _read_from_rx_buffers(self):
        """Read the next available message into the given `bytearray`

        Args:
            msg_buffer (bytearray): The buffer to load the message into
        """
        status = self._read_status()
        #self._dbg("Read Status byte:", "{:#010b}".format(status))
        # TODO: read and store all available messages
        if status & 0b1:
            self._read_rx_buffer(_READ_RX0)
            self._dbg('\tRead Buffer 0')

        if status & 0b10:
            self._read_rx_buffer(_READ_RX1)
            self._dbg('\tRead Buffer 1')



    def _write_message(self, tx_buffer, message_obj):
        if tx_buffer is None:
            raise RuntimeError("No transmit buffer available to send")
        if isinstance(message_obj, RemoteTransmissionRequest):
            dlc = message_obj.length
        else:
            dlc = len(message_obj.data)

        if dlc > _MAX_CAN_MSG_LEN:
            raise AttributeError("Message/RTR length must be <=%d" % _MAX_CAN_MSG_LEN)
        load_command = tx_buffer.LOAD_CMD

        if isinstance(message_obj, RemoteTransmissionRequest):
            dlc |= _RTR_MASK

        # this splits up the id header, dlc (len, rtr status), and message buffer
        self._load_id_buffer(message_obj.id, message_obj.extended)

        # "load_command"  is the LOAD_TX_BUFFER SPI command  
        #    here we are using this command to start writing to the TXBnSIDH register onwards 
        #print("\t\tID Buffer:", self._id_buffer)
        #print("\t\tdls      :", dlc)
        self.cs.off() 
        self.spi.write(bytes([tx_buffer.LOAD_CMD]))
        self.spi.write(self._id_buffer)                            # write the 4 bytes of the ID: TXBnSIDH, TXBnSIDL, TXBnEID8, TXBnEID0
        self.spi.write(bytes([dlc]))

        if isinstance(message_obj, Message):
            self.spi.write(message_obj.data)                   # write the data to the registers: TXBnD0-7
        self.cs.on() 

        # send the frame based on the current buffers
        self._start_transmit(tx_buffer)
        
        return True     # the message was submitted successfully.  There is no guarantee that it was received. 


    def _start_transmit(self, tx_buffer):
        # SPI command RTS (Request to send) for the specified transmit buffer
        self.cs.off() 
        self.spi.write(bytes([tx_buffer.SEND_CMD]))
        self.cs.on() 

    def _set_filter_register(self, filter_index, mask, extended):
        filter_reg_addr = FILTERS[filter_index]
        self._write_id_to_register(filter_reg_addr, mask, extended)

    def _set_mask_register(self, mask_index, mask, extended):
        mask_reg_addr = MASKS[mask_index]
        self._write_id_to_register(mask_reg_addr, mask, extended)

    @staticmethod
    def _unload_ids(raw_ids):
        """In=> 32-bit int packed with (StdID or ExTID top11  + bot18)+ extid bit
        out=> id, extended flag"""
        extended = (raw_ids & _TXB_EXIDE_M_16 << 16) > 0
        # std id field is most significant 11 bits of 4 bytes of id registers
        top_chunk = raw_ids & EXTID_TOP_11_READ_MASK
        if extended:
            # get bottom 18
            bottom_chunk = raw_ids & EXTID_BOTTOM_18_MASK
            # shift the top chunk back down 3 to start/end at bit 28=29th
            top_chunk >>= 3
            sender_id = top_chunk | bottom_chunk
        else:
            # shift down the  3 [res+extid+res]+18 extid bits
            sender_id = top_chunk >> (18 + 3)
        return (extended, sender_id)

    def _load_id_buffer(self, can_id, extended=False):
        self._id_buffer[0] = 0
        self._id_buffer[1] = 0
        self._id_buffer[2] = 0
        self._id_buffer[3] = 0

        if extended:
            extended_id = can_id
            # mask off top 11
            high_11 = extended_id & EXTID_TOP_11_WRITE_MASK
            # mask off bottom 18
            low_18 = extended_id & EXTID_BOTTOM_18_MASK
            # shift up high piece to fill MSBits and make space for extended flag
            high_11 <<= 3
            # or 'em together!
            extended_id_shifted = high_11 | low_18
            final_id = extended_id_shifted | EXTID_FLAG_MASK
            # set dat FLAG

        else:
            std_id = can_id & STDID_BOTTOM_11_MASK  # The actual ID?
            # shift up to fit all 4 bytes
            final_id = std_id << (16 + 5)

        # top = (final_id & EXTID_TOP_11_READ_MASK) >> 21
        # flags = (final_id & (0x7 << 18)) >> 18
        # bottom = final_id & EXTID_BOTTOM_18_MASK
        # print(
        #     "final final_id: 0b{top:011b} {flags:03b} {bottom:018b}".format(
        #         top=top, flags=flags, bottom=bottom
        #     )
        # )
        pack_into(">I", self._id_buffer, 0, final_id)

    def _write_id_to_register(self, register, can_id, extended=False):
        # load register in to ID buffer

        current_mode = self._mode
        self._set_mode(_MODE_CONFIG)
        # set the mask in the ID buffer

        self._load_id_buffer(can_id, extended)

        #tmp = bytearray(2)
        self.cs.off() 
        #self.spi.write_readinto(bytes([_WRITE, register]), tmp)
        self.spi.write(bytes([_WRITE, register]))
        self.spi.write(self._id_buffer)
        self.cs.on() 

        self._set_mode(current_mode)

    @property
    def _tx_buffers_in_use(self):
        # the ref code allows for reserving buffers, but didn't see any way
        # to use them. maybe un-reserve then use?
        # TODO: this should return a tuple of busy states
        # byte status = mcp2515_readStatus() & MCP_STAT_TX_PENDING_MASK
        status = self._read_status()
        #self._dbg("txbuffers in use status:", "{:#010b}".format(status))
        return (
            bool(status & _STAT_TX0_PENDING),
            bool(status & _STAT_TX1_PENDING),
            bool(status & _STAT_TX2_PENDING),
        )

    def _get_tx_buffer(self):
        """Get the address of the next available tx buffer and unset
        its interrupt bit in _CANINTF"""
        # check all buffers by looking for match on
        txs_busy = self._tx_buffers_in_use
        if all(txs_busy):
            self._dbg("none available!")
            return None
        buffer_index = txs_busy.index(False)  # => self._tx_buffers
        tx_buffer = self._tx_buffers[buffer_index]

        self._mod_register(_CANINTF, tx_buffer.INT_FLAG_MASK, 0)
        return tx_buffer

    def _set_baud_rate(self):

        # *******8 set baud rate ***********
        cnf1, cnf2, cnf3 = _BAUD_RATES[self.baudrate]

        self._set_register(_CNF1, cnf1)
        self._set_register(_CNF2, cnf2)
        self._set_register(_CNF3, cnf3)
        sleep(0.010)

    def _reset(self):
        self.cs.off() 
        self.spi.write(bytes([_RESET]))
        self.cs.on() 
        sleep(0.010)

    def _set_mode(self, mode):
        stat_reg = self._read_register(_CANSTAT)
        current_mode = stat_reg & _MODE_MASK

        if current_mode == mode:
            return
        self._timer.setTimer(5)
        while not self._timer.expired:

            new_mode_set = self._request_new_mode(mode)
            if new_mode_set:
                self._mode = mode
                return

        raise RuntimeError("Unable to change mode")

    def _request_new_mode(self, mode):
        self._timer.setTimer(0.200)
        while not self._timer.expired:
            # Request new mode
            # This is inside the loop as sometimes requesting the new mode once doesn't work
            # (usually when attempting to sleep)
            self._mod_register(_CANCTRL, _MODE_MASK, mode)

            status = self._read_register(_CANSTAT)
            if (status & _MODE_MASK) == mode:
                return True

        raise RuntimeError("Timeout setting Mode")

    def _mod_register(self, register_addr, mask, new_value):
        """There appears to be an interface on the MCP2515 that allows for
        setting a register using a mask"""
        self._buffer[0] = _BITMOD
        self._buffer[1] = register_addr
        self._buffer[2] = mask
        self._buffer[3] = new_value

        self.cs.off() 
        self.spi.write(bytes([_BITMOD, register_addr, mask, new_value]))
        self.cs.on() 


    def _read_register(self, regsiter_addr):
        """
        self._buffer[0] = _READ
        self._buffer[1] = regsiter_addr

        self.cs.off() 
        self.spi.write(bytes([_READ, regsiter_addr]))
        self._buffer[0] = 0
        tmp = bytearray(1)
        self.spi.write_readinto(bytes([0]), tmp)
        self.cs.on() 
        self._buffer[0] = tmp[0]

        return self._buffer[0]
        """
        self.cs.off() 
        self.spi.write(bytes([_READ, regsiter_addr]))
        regVal = self.spi.read(1)
        self.cs.on()

        return int.from_bytes(regVal, 'big')




    def _read_status(self):
        """
        self._buffer[0] = _READ_STATUS
        self.cs.off() 
        self.spi.write(bytes([_READ_STATUS]))
        var = self.spi.read(1)
        self.cs.on() 
        self._buffer[0] = var[0]
        return self._buffer[0]
        """
        self.cs.off() 
        self.spi.write(bytes([_READ_STATUS]))
        regVal = self.spi.read(1)
        self.cs.on()

        return int.from_bytes(regVal, 'big')
        


    def _set_register(self, regsiter_addr, register_value):
        self.cs.off()
        self.spi.write(bytes([_WRITE, regsiter_addr, register_value]))
        self.cs.on()


    def _get_bus_status(self):
        """Get the status flags that report the state of the bus"""
        bus_flags = self._read_register(_EFLG)

        flags = []
        for idx in range(8):
            bit_mask = 1 << idx
            flags.append((bus_flags & bit_mask) > 0)
        (  # pylint:disable=unbalanced-tuple-unpacking
            error_warn,
            _rx_error_warn,
            _tx_err_warn,
            rx_error_passive,
            tx_error_passive,
            buss_off,
            self._rx0_overflow,
            self._rx1_overflow,
        ) = flags
        if self._rx0_overflow or self._rx0_overflow:
            self._mod_register(
                _EFLG, 0xC0, 0
            )  # clear overflow bits now that we've recorded them

        if buss_off:
            self._bus_state = BusState.BUS_OFF
        elif tx_error_passive or rx_error_passive:
            self._bus_state = BusState.ERROR_PASSIVE
        elif error_warn:
            self._bus_state = BusState.ERROR_WARNING
        else:
            self._bus_state = BusState.ERROR_ACTIVE

    def _create_mask(self, match):
        mask = match.mask
        if mask == 0:
            if match.extended:
                mask = EXTID_BOTTOM_29_MASK
            else:
                mask = STDID_BOTTOM_11_MASK

        masks_used = len(self._masks_in_use)
        if masks_used < len(MASKS):
            next_mask_index = masks_used

            self._set_mask_register(next_mask_index, mask, match.extended)
            self._masks_in_use.append(MASKS[next_mask_index])
            return next_mask_index

        raise RuntimeError("No Masks Available")

    def _create_filter(self, match, mask_index):

        next_filter_index = len(self._filters_in_use[mask_index])
        if next_filter_index == len(FILTERS[mask_index]):
            raise RuntimeError("No Filters Available")

        filter_register = FILTERS[mask_index][next_filter_index]

        self._write_id_to_register(filter_register, match.address, match.extended)
        self._filters_in_use[mask_index].append(filter_register)

    def deinit_filtering_registers(self):
        """Clears the Receive Mask and Filter Registers"""

        for mask_index, mask_reg in enumerate(MASKS):
            self._set_register(mask_reg, 0)

            for filter_reg in FILTERS[mask_index]:
                self._set_register(filter_reg, 0)
        self._masks_in_use = []
        self._filters_in_use = [[], []]

    ######## CANIO API METHODS #############
    @property
    def baudrate(self):
        """ The baud rate (read-only)"""
        return self._baudrate

    @property
    def transmit_error_count(self):
        """ The number of transmit errors (read-only). Increased for a detected transmission error,\
             decreased for successful transmission. Limited to the range from 0 to 255 inclusive. \
                 Also called TEC."""
        return self._read_register(_TEC)

    @property
    def receive_error_count(self):
        """ The number of receive errors (read-only). Increased for a detected reception error, \
            decreased for successful reception. Limited to the range from 0 to 255 inclusive. Also
         called REC."""
        return self._read_register(_REC)

    @property
    def error_warning_state_count(self):
        """Not supported by hardware. Raises an `AttributeError` if called"""
        raise AttributeError("`error_warning_state_count` not supported by hardware")

    @property
    def error_passive_state_count(self):
        """Not supported by hardware. Raises an `AttributeError` if called"""
        raise AttributeError("`error_passive_state_count` not supported by hardware")

    @property
    def bus_off_state_count(self):
        """Not supported by hardware. Raises an `AttributeError` if called"""
        raise AttributeError("`bus_off_state_count` not supported by hardware")

    @property
    def state(self):  # State
        """The current state of the bus. (read-only) """
        self._get_bus_status()
        return self._bus_state

    @property
    def loopback(self):  # bool
        """True if the device was created in loopback mode, False otherwise. (read-only)"""
        return self._loopback

    @property
    def silent(self):  # bool
        """True if the device was created in silent mode, False otherwise. (read-only)"""
        return self._silent

    def restart(self):
        """If the device is in the bus off state, restart it."""
        self.initialize()

    def listen(self, matches=None, *, timeout: float = 10):
        """Start receiving messages that match any one of the filters.

        Creating a listener is an expensive operation and can interfere with reception of messages
        by other listeners.

    There is an implementation-defined maximum number of listeners and limit to the complexity of
    the filters.

    If the hardware cannot support all the requested matches, a ValueError is raised. Note that \
        generally there are some number of hardware filters shared among all fifos.

    A message can be received by at most one Listener. If more than one listener matches a message,\
         it is undefined which one actually receives it.

    An empty filter list causes all messages to be accepted.

    Timeout dictates how long ``receive()`` will block.

        Args:
            match (Optional[Sequence[Match]], optional): [description]. Defaults to None.
            timeout (float, optional): [description]. Defaults to 10.

        Returns:
            Listener: [description]
        """
        if matches is None:
            matches = []
        elif self.silent and not self.loopback:
            raise AttributeError(
                "Hardware does not support setting `matches` in when\
                `silent`==`True` and `loopback` == `False`"
            )

        for match in matches:
            self._dbg("match:", match)
            mask_index_used = self._create_mask(match)
            self._create_filter(match, mask_index=mask_index_used)

        used_masks = len(self._masks_in_use)
        # if matches were made and there are unused masks
        # set the unused masks to prevent them from leaking packets
        if len(matches) > 0 and used_masks < len(MASKS):
            next_mask_index = used_masks
            for idx in range(next_mask_index, len(MASKS)):
                #print("using unused mask index:", idx)
                self._create_mask(matches[-1])

        return Listener(self, timeout)

    #def deinit(self):
    #    """Deinitialize this object, freeing its hardware resources"""
    #    self._cs_pin.deinit()

    def __enter__(self):
        """Returns self, to allow the object to be used in a The with statement statement for \
            resource control"""
        return self

    #def __exit__(self, unused1, unused2, unused3):
    #    """Calls deinit()"""
    #    self.deinit()

    ##################### End canio API ################

    def _dbg(self, *args, **kwargs):
        if self._debug:
            print("DBG::\t\t", *args, **kwargs)

    def _tx_buffer_status_decode(self, status_byte):
        out_str = "Status: "
        # when CAN_H is disconnected?: 0x18
        out_str += "\nStatus of chosen buffer: %s\n" % hex(status_byte)
        if status_byte & 0x40:
            out_str += " Message ABORTED"
        if status_byte & 0x20:
            out_str += " Message LOST ARBITRATION"
        if status_byte & 0x10:
            out_str += " TRANSMIT ERROR"
        if status_byte & 0x8:
            out_str += " Transmit Requested"
        else:
            out_str += " Message sent"
        out_str += " Priority: " + ["LAST", "LOW", "MEDIUM", "HIGH"][status_byte & 0x3]

        return out_str
