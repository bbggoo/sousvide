from micropython import const
import ssd1306
from ssd1306 import SSD1306_SPI
import font

SET_LOW_COLUMN      = const(0x00)
SET_HIGH_COLUMN     = const(0x10)
SET_PAGE_ADDR_SH1106 = const(0xb0)
#SET_DISP_START_LINE = const(0x40)
 
class SH1106_SPI(SSD1306_SPI):
    def show(self):
        for pg in range(0, self.pages):
            for cmd in (
                SET_PAGE_ADDR_SH1106 | pg,
                SET_LOW_COLUMN | 2,
                SET_HIGH_COLUMN | 0,
                ):
                self.write_cmd(cmd)
            self.write_data(self.buffer[pg * 0x80:(pg + 1) * 0x80])

#中文字库,GT20L16S1Y
#sh1106_spi.py
##GND VCC D0 D1 RES DC CS
#vcc 3.3V
#//DC引脚输入高，表示写数据  
#//DC引脚输入低，表示写命令  
##SDI(数据输入)、SDO(数据输出)、SCLK(时钟)、CS(片选)。
#(1)SDO/MOSI （（master out slaver in））– 主设备数据输出，从设备数据输入;
#(2)SDI/MISO – 主设备数据输入，从设备数据输出;
#(3)SCLK – 时钟信号，由主设备产生;
#(4)CS/SS – 从设备使能信号，由主设备控制。当有多个从设备的时候，因为每个从设 备上都有一个片选引脚接入到主设备机中，
# 当我们的主设备和某个从设备通信时将需 要将从设备对应的片选引脚电平拉低或者是拉高。
#我做的板子cs直接接地.
#sck(sclk)接gpio 18, mosi接gpio 23, res接的io 15 ,dc接的io 16, 至于程序里面dc我分配了引脚,是因为现在还没搞清楚怎样丢给它一个None,
# 我直接赋值None不行,直接丢个空的io给它吧.
#中文字库OLED     Arduino UNO
# GND                    GND                 地
# VCC                    VCC                 电源正 接到3.3或5.0
# CLK                    18                  时钟
# MOSI                   23                  数据
# MISO                   19                  –主设备数据输入，从设备数据输出
# DC                     16                   选择指令或数据 (u8g配置中的A0)
# CS1                    5                  屏幕片选
# FSO                    12?                  字库输出
# CS2                    8?                   字库片选


