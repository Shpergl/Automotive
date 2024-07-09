# Pelican - CAN interface class
# Author: Oleksandr Ivanchuk
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import time
from machine import Pin, SPI


class CAN:
    '''
    Implements the standard CAN communication protocol.
    '''

    def __init__(self, spi_id, baud, sck, mosi, miso, cs) -> None:
        '''
        MCP2515 chip initialization

        SPI used by default is HSPI
        id=1, baudrate=10000000, sck=14, mosi=13, miso=12

        CS default is pin 27
        '''
        self.spi = SPI(spi_id, baud, sck=Pin(sck), mosi=Pin(mosi), miso=Pin(miso))
        self.spi.init()

        self.cs = Pin(cs, Pin.OUT, value=1)

        self._rx_buf = []

        # Software reset
        self._spi_reset()

        # If you can read the data, it is considered that the initialization
        # is OK. At least the chip is soldered.
        time.sleep(0.2)
        mode = self._spi_read_reg(b'\x0e')
        if (mode == 0):
            raise OSError("MCP2515 init failed (Cannot read any data).")


    def stop(self) -> None:
        '''
        Stops MCP2515
        '''
        self._spi_write_bit(b'\x0f', b'\xe0', b'\x20')  # sleep mode


    def start(self,
              speed_cfg: int = 500,
              crystal: int = 8,
              filter=None,
              listen_only: bool = False) -> None:
        '''
        Starts MCP2515

        speed_cfg: CAN communication speed in Kb/s
        The supported communication speeds are as follows:
            - for 16MHz Crystal Oscillator
        5, 10, 20, 33, 40, 50, 80, 95, 100, 125, 200, 250, 500, 1000
            - for 8MHz Crystal Oscillator
        5, 10, 20, 40, 50, 80, 100, 125, 200, 250, 500

        crystal: defines the frequency of the Crystal Oscillator
                 could be either 8 or 16 MHz

        filter: filter mode for received packets
        TODO

        listen_only: whether to specify the listening mode
        '''
        # Set to configuration mode
        self._spi_reset()
        self._spi_write_bit(b'\x0f', b'\xe0', b'\x80')

        # Set communication rate
        self._set_speed(speed_cfg, crystal)

        # Channel 1 packet filtering settings
        if (filter == None):
            # RXB0CTRL = 0x60
            self._spi_write_bit(b'\x60', b'\x64', b'\x64')
        else:
            self._spi_write_bit(b'\x60', b'\x64', b'\x04')
            self._spi_write_reg(b'\x00', filter.get('F0'))
            self._spi_write_reg(b'\x04', filter.get('F1'))
            self._spi_write_reg(b'\x20', filter.get('M0'))

            def _spi_write_bit(self, addr, mask, value):
                '''
                MCP2515_SPI instruction-bit modification
                '''
                self.cs.off()
                self.spi.write(self.BIT_MODIFY)
                self.spi.write(addr)
                self.spi.write(mask)
                self.spi.write(value)
                self.cs.on()

        # Disable channel 2 message reception
        self._spi_write_bit(b'\x70', b'\x60', b'\x00')
        self._spi_write_reg(b'\x08', b'\xff\xff\xff\xff')
        self._spi_write_reg(b'\x10', b'\xff\xff\xff\xff')
        self._spi_write_reg(b'\x14', b'\xff\xff\xff\xff')
        self._spi_write_reg(b'\x18', b'\xff\xff\xff\xff')
        self._spi_write_reg(b'\x24', b'\xff\xff\xff\xff')

        # Set to normal mode or listening mode
        mode = b'\x60' if listen_only else b'\x00'
        self._spi_write_bit(b'\x0f', b'\xe0', mode)

        self.set_interrupt()
        #self._spi_write_bit(b'\x2b', b'\x01', b'\x01')
        #self._spi_write_bit(b'\x2b', b'\xff', b'\xff')

    def set_interrupt(self, mode=b'\x03'):
        self._spi_write_bit(b'\x2b', mode, mode)

    # def clear_iterrupt(self):
    #     self._spi_write_bit(b'\x2c', b'\x03', b'\x00')


    def _set_speed(self,
                   speed_cfg: int,
                   crystal: int) -> None:
        '''
        Sets communication rate according to used oscillator.
        https://kvaser.com/support/calculators/bit-timing-calculator/
        Set MCP2510 chip and desired bitrate, choose parameter with SP% = 75 and SJW = 1
        Reverse registers order. <bitrate>: b'<CNF3><CNF2><CNF1>'
        '''
        speed_cfg_at_16M = {
            1000: b'\x82\xD0\x00',
            500: b'\x86\xF0\x00',
            250: b'\x85\xF1\x41',
            200: b'\x87\xFA\x01',
            125: b'\x86\xF0\x03',
            100: b'\x87\xFA\x03',
            95: b'\x07\xAD\x03',
            80: b'\x87\xFF\x03',
            50: b'\x87\xFA\x07',
            40: b'\x87\xFF\x07',
            33: b'\x07\xBE\x09',
            20: b'\x87\xFF\x0F',
            10: b'\x87\xFF\x1F',
            5: b'\x87\xFF\x3F'
        }

        speed_cfg_at_8M = {
            500: b'\x01\x91\x00',
            250: b'\x03\xac\x00',
            200: b'\x04\xb6\x00',
            125: b'\x03\xac\x01',
            100: b'\x04\xb6\x01',
            80: b'\x02\x92\x04',
            50: b'\x04\xb6\x03',
            47619: b'\x02\x9b\x06',
            40: b'\x04\xb6\x04',
            20: b'\x04\xb6\x09',
            10: b'\x04\xb6\x13',
            5: b'\x04\xb6\x27'
        }

        speed = {
            8: speed_cfg_at_8M,
            16: speed_cfg_at_16M
        }
        if crystal in speed.keys():
            if speed_cfg in speed[crystal].keys():
                cfg = speed[crystal].get(speed_cfg, (b'\x00\x00\x00'))
                print(cfg)
                self._spi_write_reg(self.CNF3_ADDR, cfg)
            else:
                raise Exception('Unsupported speed ({}Kb/s) or oscillator \
settings incorrect.'.format(speed_cfg))
        else:
            raise Exception('Unsupported Crystal Oscillator frequency. \
select from {}'.format(''.join(speed.keys())))

        del speed


    def send_msg(self, msg: dict, send_chanel: int = None) -> None:
        '''
        Send a message.

        msg:
        msg ['id']: ID of the message to be sent
        msg ['ext']: Whether the message to be sent is an extended frame
        msg ['data']: Data of the message to be sent
        msg ['dlc']: Length of the message to be sent
        msg ['rtr']: Whether the message to be sent is a remote frame

        send_chanel:
        Specify the channel for sending packets. The valid values ​​are
        as follows:
        0: channel 0
        1: Channel 1
        2: Channel 2
        MCP2515 provides three sending channels. By default, channel 0 is used.
        TODO: automatically find free channels.
        NOTE: If there are pending messages in the channel, the previous
        message transmission will be stopped.
        Then replace it with a new message and enter the pending state again.
        '''
        if send_chanel == None:
            send_chanel = 0
        # stop message transmission in previous register
        ctl = (((send_chanel % 3) + 3) << 4) .to_bytes(1, 'big')
        self._spi_write_bit(ctl, b'\x08', b'\x00')
        # Data structure
        self.tx_buf = bytearray(13)
        if msg.get('ext'):
            self.tx_buf[0] = ((msg.get('id')) >> 21) & 0xFF
            id_buf = ((msg.get('id')) >> 13) & 0xE0
            id_buf |= 0x08
            id_buf |= ((msg.get('id')) >> 16) & 0x03
            self.tx_buf[1] = id_buf
            self.tx_buf[2] = ((msg.get('id')) >> 8) & 0xFF
            self.tx_buf[3] = (msg.get('id')) & 0xFF
            if msg.get('rtr'):
                self.tx_buf[4] |= 0x40
        else:
            self.tx_buf[0] = ((msg.get('id')) >> 3) & 0xFF
            self.tx_buf[1] = ((msg.get('id')) << 5) & 0xE0
            if msg.get('rtr'):
                self.tx_buf[1] |= 0x10
        if msg.get('rtr') == False:
            self.tx_buf[4] |= msg.get('dlc') & 0x0F
            self.tx_buf[5:13] = msg.get('data')[: msg.get('dlc')]
        # Data loading
        dat = ((((send_chanel % 3) + 3) << 4) + 1) .to_bytes(1, 'big')
        self._spi_write_reg(dat, self.tx_buf)
        # Send
        # self._spi_write_bit (ctl, b'\x08', b'\x08')
        self._spi_send_msg(1 << send_chanel)


    def recv_msg(self) -> dict:
        '''
        Requests whether the MCP2515 has received a message. If so, read it
        in buffer. check_rx is called.
        Requests whether the buffer has packets. If yes, return the earliest
        received frame, otherwise return None.

        Return Msg description:
        msg ['tm']: Time to receive the message [ms]. Timer starts on power on.
        msg ['id']: ID of the received message
        msg ['ext']: Whether the received message is an extended frame
        msg ['data']: Received message data
        msg ['dlc']: Length of received message
        msg ['rtr']: Whether the received message is a remote frame
        NOTE: Only one frame is returned at a time.
        '''
        self.check_rx()
        print('recv_msg rx_buf:{}'.format(len(self._rx_buf)))
        if len(self._rx_buf) == 0:
            return None
        dat = self._rx_buf.pop(0)

        msg = {}
        msg['tm'] = int.from_bytes(dat[-8:], 'big')
        msg['dlc'] = int.from_bytes(dat[4: 5], 'big') & 0x0F
        msg['data'] = dat[5:13]
        # 0: standard frame 1: extended frame
        ide = (int.from_bytes(dat[1: 2], 'big') >> 3) & 0x01
        msg['ext'] = True if ide == 1 else False
        id_s0_s10 = int.from_bytes(dat[: 2], 'big') >> 5
        id_e16_e17 = int.from_bytes(dat[: 2], 'big') & 0x03
        id_e0_e15 = int.from_bytes(dat[2: 4], 'big')
        if msg['ext']:
            msg['id'] = (id_s0_s10 << 18) + (id_e16_e17 << 16) + id_e0_e15
            msg['rtr'] = True if (int.from_bytes(
                dat[4: 5], 'big') & 0x40) else False
        else:
            msg['id'] = id_s0_s10
            msg['rtr'] = True if (int.from_bytes(
                dat[1: 2], 'big') & 0x10) else False
        #self.clear_iterrupt()
        return msg

    def process_msg(self, packet) -> dict:
        '''
        Requests whether the MCP2515 has received a message. If so, read it
        in buffer. check_rx is called.
        Requests whether the buffer has packets. If yes, return the earliest
        received frame, otherwise return None.

        Return Msg description:
        msg ['tm']: Time to receive the message [ms]. Timer starts on power on.
        msg ['id']: ID of the received message
        msg ['ext']: Whether the received message is an extended frame
        msg ['data']: Received message data
        msg ['dlc']: Length of received message
        msg ['rtr']: Whether the received message is a remote frame
        NOTE: Only one frame is returned at a time.
        '''

        msg = {}
        msg['tm'] = int.from_bytes(packet[-8:], 'big')
        msg['dlc'] = int.from_bytes(packet[4: 5], 'big') & 0x0F
        msg['data'] = packet[5:13]
        # 0: standard frame 1: extended frame
        ide = (int.from_bytes(packet[1: 2], 'big') >> 3) & 0x01
        msg['ext'] = True if ide == 1 else False
        id_s0_s10 = int.from_bytes(packet[: 2], 'big') >> 5
        id_e16_e17 = int.from_bytes(packet[: 2], 'big') & 0x03
        id_e0_e15 = int.from_bytes(packet[2: 4], 'big')
        if msg['ext']:
            msg['id'] = (id_s0_s10 << 18) + (id_e16_e17 << 16) + id_e0_e15
            msg['rtr'] = True if (int.from_bytes(
                packet[4: 5], 'big') & 0x40) else False
        else:
            msg['id'] = id_s0_s10
            msg['rtr'] = True if (int.from_bytes(
                packet[1: 2], 'big') & 0x10) else False
        return msg


    def get_smpl(self, printable=True):
        '''
        Query whether the MCP2515 has received a message. If so, deposit it in Buf. check_rx is called.
        Query whether Buf has packets. If yes, return the earliest received frame, otherwise return None.
        Return Msg description:
        '''
        self.check_rx()
        if len(self._rx_buf) == 0:

            return None
        dat = self._rx_buf.pop(0)
        msg = {}

        msg['dlc'] = int.from_bytes(dat[4: 5], 'big') & 0x0F
        msg['data'] = dat[5:13]
        msg['id'] = int.from_bytes(dat[: 2], 'big') >> 5

        if printable:
            return '{}  [{}]  {}'.format(hex(msg['id']), msg['dlc'], msg['data'].decode())
        else:
            return msg


    def get_msg(self):
        #rx_flag = int.from_bytes(self._spi_ReadStatus(), 'big')
        #if (rx_flag & 0x01):
        dat = self._spi_RecvMsg(0)
        dat2 = self._spi_RecvMsg(1)
        #tm = (time.ticks_ms()).to_bytes(8, 'big')
        data = self.process_msg(dat)
        return data


        # if (rx_flag & 0x02):
        #     dat = self._spi_RecvMsg(1)
        #     tm = (time.ticks_ms()).to_bytes(8, 'big')
        #     return self.process_msg(dat + tm)



    def check_rx(self):
        '''
        Query whether the MCP2515 has received a message. If so, store it in Buf and return TRUE, otherwise return False.
        Note: Failure to store the messages in the MCP into Buf in time may result in the MCP being unable to receive new messages.
        In other words, packets may be lost.
        So, try to call this function as much as possible ~~
        '''
        rx_flag = int.from_bytes(self._spi_ReadStatus(), 'big')
        if (rx_flag & 0x01):
            dat = self._spi_RecvMsg(0)
            #tm = (time.ticks_ms()).to_bytes(8, 'big')
            #self._rx_buf.(dat + tm)
            self._rx_buf.extend(dat)
        if (rx_flag & 0x02):
            dat = self._spi_RecvMsg(1)
            #tm = (time.ticks_ms()).to_bytes(8, 'big')
            #self._rx_buf.append(dat + tm)
            self._rx_buf.extend(dat)
        if (rx_flag & 0x03):
            dat = self._spi_RecvMsg(2)
            self._rx_buf.extend(dat)

        return True if (rx_flag & 0b11000000) else False

    RESET = b'\xc0'  # 1100 0000
    READ  = b'\x03' #  0000 0011
    WRITE  = b'\x02' #  0000 0010
    BIT_MODIFY = b'\x05' #  0000 0101
    READ_STATUS = b'\xa0' #  1010 0000
    READ_RX_STATUS = b'\xb0' #  1011 0000
    CNF1_ADDR  = b'\x2a' #  CONFIGURATION REGISTER 1
    CNF2_ADDR  = b'\x29' #  CONFIGURATION REGISTER 2
    CNF3_ADDR  = b'\x28' #  CONFIGURATION REGISTER 3
    can_stat = b'\x21'

    def _spi_reset(self):
        '''
        MCP2515_SPI instruction-reset
        '''
        self.cs.off()
        self.spi.write(self.RESET)
        self.cs.on()


    def _spi_write_reg(self, addr, value):
        '''
        MCP2515_SPI instruction-write register
        '''
        self.cs.off()
        #self._spi_write_reg(b'\x28', cfg) cfg = b'\x01\x91\x00'
        # 0000 0001 1001 0001 0000 0000
        self.spi.write(self.WRITE)
        self.spi.write(addr)
        self.spi.write(value)
        self.cs.on()

        #''.join(format(ord(byte), '08b') for byte in b'\xf0\xf1')

        # self._spi_write_reg(b'\x28', b'\x01\x91\x00')
        # 500: b'\x01\x91\x00',

    def _spi_read_reg(self, addr, num=1):
        '''
        MCP2515_SPI instruction-read register
        '''
        self.cs.off()
        self.spi.write(self.READ)
        self.spi.write(addr)
        buf = self.spi.read(num)
        self.cs.on()
        return buf


    def _spi_write_bit(self, addr, mask, value):
        '''
        MCP2515_SPI instruction-bit modification
        '''
        self.cs.off()
        self.spi.write(self.BIT_MODIFY)
        self.spi.write(addr)
        self.spi.write(mask)
        self.spi.write(value)
        self.cs.on()


    def _spi_ReadStatus(self):
        '''
        MCP2515_SPI instruction-read status
        '''
        self.cs.off()
        self.spi.write(self.READ_STATUS)
        buf = self.spi.read(1)
        print('_spi_ReadStatus: {}'.format(buf))
        self.cs.on()
        return buf


    def _spi_RecvMsg(self, select):
        '''
        MCP2515_SPI instruction-read Rx buffer
        '''
        self.cs.off()
        buf = []
        if select == 0:
            self.spi.write(b'\x90') #  1001 0000
            #self.spi.write(b'\x92') #  1001 0010
            buf.append(self.spi.read(8))
        if select == 1:
            self.spi.write(b'\x94') #  1001 0100
            buf.append(self.spi.read(8))
        elif select == 2:
            self.spi.write(b'\x90')  # 1001 0000
            # self.spi.write(b'\x92') #  1001 0010
            buf.append(self.spi.read(8))
            self.spi.write(b'\x94')  # 1001 0100
            buf.append(self.spi.read(8))
        self.cs.on()
        print('_spi_RecvMsg: {}'.format(buf))
        return buf

    def _spi_RecvMsg2(self, select):
        '''
        MCP2515_SPI instruction-read Rx buffer
        '''
        self.cs.off()
        self.spi.write(b'\x94')  # 1001 0100
        buf = self.spi.read(8)
        print('_spi_RecvMsg RXB1SIDH: {}'.format(buf))
        self.spi.write(b'\x96')  # 1001 0110
        buf = self.spi.read(8)
        print('_spi_RecvMsg RXB1D0: {}'.format(buf))


        self.spi.write(b'\x90') #  1001 0000
        buf = self.spi.read(8)
        print('_spi_RecvMsg RXB0SIDH: {}'.format(buf))
        self.spi.write(b'\x92') #  1001 0010
        buf = self.spi.read(8)
        print('_spi_RecvMsg RXB0D0: {}'.format(buf))


        self.cs.on()
        print('_spi_RecvMsg: {}'.format(buf))
        return buf


    def _spi_send_msg(self, select):
        '''
        MCP2515_SPI instruction-Request to send a message
        '''
        self.cs.off()
        self.spi.write((0x80 + (select & 0x07)). to_bytes(1, 'big'))
        self.cs.on()
