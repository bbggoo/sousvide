# winbond.py
from micropython import const
from machine import Pin, SPI
import time   
import machine    
#
# spiflash.py
#
# Adapted from https://github.com/manitou48/pyboard
#
# SPI flash http://www.adafruit.com/product/1564
# SPI 1 42mhz max   SPI 2  21 mhz max
# SPI1 X5-X8 CS CLK MISO MOSI   3.3v grnd

__all__ = ('SPIFLash',)

CMD_JEDEC_ID = const(0x9F)
CMD_READ_STATUS = const(0x05)    # Read status register
CMD_READ = const(0x03)           # Read @ low speed
CMD_READ_HI_SPEED = const(0x0B)  # Read @ high speed
CMD_WRITE_ENABLE = const(0x06)   # Write enable
CMD_PROGRAM_PAGE = const(0x02)   # Write page
CMD_ERASE_4K = const(0x20)
CMD_ERASE_32K = const(0x52)
CMD_ERASE_64K = const(0xD8)
CMD_ERASE_CHIP = const(0xC7)
CMD_READ_UID = const(0x4B)
PAGE_SIZE = const(256)
oled_cs=Pin(15)
COMMANDS = {
    '4k': CMD_ERASE_4K,
    '32k': CMD_ERASE_32K,
    '64k': CMD_ERASE_64K
}


class SPIFlash:
    def __init__(self, spi, cs,oled_cs):
        self._spi = spi
        cs = Pin(cs, Pin.OUT, pull=Pin.PULL_UP)
        self._cs = cs
        self._cs.value(1)
        #self._sck =Pin(14)
        #self._sck.value(1)
        #self._mosi=Pin(13)
        #self._mosi.value(1)
        #self._miso=Pin(12)
        oled_cs.value(1)
        self._buf = bytearray([0])

    def _write(self, val):
        if isinstance(val, int):
            self._buf[0] = val
            self._spi.write(self._buf)
        else:
            self._spi.write(val)

    def read_block(self, addr, buf):
        #state=machine.disable_irq()
        #oled_cs.value(1)
        self._cs.value(0)
        self._write(CMD_READ_HI_SPEED)
        #self._write(CMD_READ)
        #通过串行数据输入引脚（SI）移位输入，每一位在串行时钟（SCLK）上升沿被锁存。
        # 然后该地址的字节数据通过串行数据输出引脚（SO）移位输出，每一位在串行时钟（SCLK）下降沿被移出。
        #self._sck.value(1)
        #self._mosi.value(1)
        #self._miso.value(1)
        self._write((addr >> 16) & 0xff)
        self._write((addr >> 8) & 0xff)
        self._write(addr & 0xff)
        self._write(0x8d)
        self._write(0x00)
        #self._miso.value(0)
        self._spi.readinto(buf)
        self._cs.value(1)
        #machine.enable_irq(state) 

    def read_bytes_high_speed(self, addr, buf):
        #oled_cs.value(1)
        #self.SPI0_clear()
        self._cs.value(0)
        self._write(CMD_READ_HI_SPEED)
        self._write(addr >> 16)
        self._write(addr >> 8)
        self._write(addr)        
        self._spi.readinto(buf)
        '''
        #如果片选信号（CS#）继续保持为低，则下一个地址的字节数据继续通过串行数据输出引
        脚（SO）移位输出。例：读取一个 15x16 点阵汉字需要 32Byte，则连续 32 个字节读取后
        结束一个汉字的点阵数据读取操作。
        如果不需要继续读取数据，则把片选信号（CS#）变为高，结束本次操作。
        '''
        self._cs.value(1)

    def getid(self):
        self._cs.value(0)
        self._write(CMD_JEDEC_ID)  # id
        res = self._spi.read(3)
        self._cs.value(1)
        return res

    def wait(self):
        while True:
            self._cs.value(0)
            self._write(CMD_READ_STATUS)
            r = self._spi.read(1)[0]
            self._cs.value(1)

            if r == 0:
                return

    def write_block(self, addr, buf):
        # Write in 256-byte chunks
        # XXX: Should check that write doesn't go past end of flash ...
        length = len(buf)
        pos = 0

        while pos < length:
            size = min(length - pos, PAGE_SIZE)
            self._cs.value(0)
            self._write(CMD_WRITE_ENABLE)
            self._cs.value(1)

            self._cs.value(0)
            self._write(CMD_PROGRAM_PAGE)
            self._write(addr >> 16)
            self._write(addr >> 8)
            self._write(addr)
            self._write(buf[pos:pos + size])
            self._cs.value(1)
            self.wait()

            addr += size
            pos += size

    def erase(self, addr, cmd):
        self._cs.value(0)
        self._write(CMD_WRITE_ENABLE)
        self._cs.value(1)

        self._cs.value(0)
        self._write(COMMANDS[cmd])
        self._write(addr >> 16)
        self._write(addr >> 8)
        self._write(addr)
        self._cs.value(1)
        self.wait()

    def erase_chip(self):
        self._cs.value(0)
        self._write(CMD_WRITE_ENABLE)
        self._cs.value(1)

        self._cs.value(0)
        self._write(CMD_ERASE_CHIP)
        self._cs.value(1)
        self.wait()