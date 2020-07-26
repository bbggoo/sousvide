
# MicroPython SSD1306 OLED driver, I2C and SPI interfaces

from micropython import const
import framebuf
import font
import math

import sys 
import gc
import ubinascii
from machine import Pin, SPI
import utime
from spiflash import SPIFlash

#sys.setrecursionlimit(100000)
# register definitions
SET_CONTRAST        = const(0x81)
SET_ENTIRE_ON       = const(0xa4)
SET_NORM_INV        = const(0xa6)
SET_DISP            = const(0xae)
SET_MEM_ADDR        = const(0x20)
#SET_COL_ADDR        = const(0x10)
SET_COL_ADDR        = const(0x21)
#SET_PAGE_ADDR       = const(0xb0)
SET_PAGE_ADDR       = const(0x22)
SET_DISP_START_LINE = const(0x40)
SET_SEG_REMAP       = const(0xa0)
SET_MUX_RATIO       = const(0xa8)
SET_COM_OUT_DIR     = const(0xc0)
SET_DISP_OFFSET     = const(0xd3)
SET_COM_PIN_CFG     = const(0xda)
SET_DISP_CLK_DIV    = const(0xd5)
SET_PRECHARGE       = const(0xd9)
SET_VCOM_DESEL      = const(0xdb)
SET_CHARGE_PUMP     = const(0x8d)
#hardware scroll
SET_HWSCROLL_OFF    = const(0x2e)
SET_HWSCROLL_ON     = const(0x2f)
SET_HWSCROLL_RIGHT  = const(0x26)
SET_HWSCROLL_LEFT   = const(0x27)
#SET_HWSCROLL_VR     = const(0x29)
#SET_HWSCROLL_VL     = const(0x2a)

#OLED_GRAM =[[0x00 for x in range(8)] for y in range(128)]
# Subclassing FrameBuffer provides support for graphics primitives
# http://docs.micropython.org/en/latest/pyboard/library/framebuf.html
class SSD1306(framebuf.FrameBuffer):
    def __init__(self, width, height, external_vcc):
        self.width = width
        self.height = height
        self.external_vcc = external_vcc
        self.pages = self.height // 8
        self.buffer = bytearray(self.pages * self.width)
        self.framebuf = framebuf.FrameBuffer1(self.buffer, self.width, self.height)
        super().__init__(self.buffer, self.width, self.height, framebuf.MONO_VLSB)
        self.init_display()

    def init_display(self):
        for cmd in (
            SET_DISP | 0x00, # off
            # address setting
            SET_MEM_ADDR, 0x00, # horizontal
            # resolution and layout
            SET_DISP_START_LINE | 0x00,
            SET_SEG_REMAP | 0x01, # column addr 127 mapped to SEG0
            SET_MUX_RATIO, self.height - 1,
            #这个是发送报文到串口的，调试后不能关闭，否则图像颠倒
            SET_COM_OUT_DIR | 0x08, # scan from COM[N] to COM0
            SET_DISP_OFFSET, 0x00,
            SET_COM_PIN_CFG, 0x02 if self.height == 32 else 0x12,
            # timing and driving scheme
            SET_DISP_CLK_DIV, 0x80,
            SET_PRECHARGE, 0x22 if self.external_vcc else 0xf1,
            SET_VCOM_DESEL, 0x30, # 0.83*Vcc
            # display
            SET_CONTRAST, 0xff, # maximum
            SET_ENTIRE_ON, # output follows RAM contents
            SET_NORM_INV, # not inverted
            # charge pump
            SET_CHARGE_PUMP, 0x10 if self.external_vcc else 0x14,
            SET_DISP | 0x01): # on
            self.write_cmd(cmd)
        self.fill(0)
        self.show()
    #关屏
    def poweroff(self):
        self.write_cmd(SET_DISP | 0x00)

    def poweron(self):
        self.write_cmd(SET_DISP | 0x01)
    #调整亮度。0最暗，255最亮
    def contrast(self, contrast):
        self.write_cmd(SET_CONTRAST)
        self.write_cmd(contrast)
    #奇数时反相显示，偶数时正常显示
    def invert(self, invert):
        self.write_cmd(SET_NORM_INV | (invert & 1))

    def show(self):
        x0 = 0
        x1 = self.width - 1
        if self.width == 64:
            # displays with width of 64 pixels are shifted by 32
            x0 += 32
            x1 += 32
        self.write_cmd(SET_COL_ADDR)
        self.write_cmd(x0)
        self.write_cmd(x1)
        self.write_cmd(SET_PAGE_ADDR)
        self.write_cmd(0)
        self.write_cmd(self.pages - 1)
        self.write_data(self.buffer)
    #col=0，清空屏幕，col大于0，填充屏幕 
    def fill(self, col):
        self.framebuf.fill(col)

    #画点,col表示颜色，0不亮或者1亮
    def pixel(self, x, y, col):
        self.pixel(x, y, col)
        
    #画点,col表示颜色，0不亮或者1亮
    def rect_zone(self, x1, y1,x2,y2,col):
        for i in range(x1,x2):
            for j in range(y1,y2):
                self.pixel(i, j, col)
               
   # 滚动
    def scroll(self, dx, dy):
        self.framebuf.scroll(dx, dy)

    def text(self, string, x, y, col=1):

        self.framebuf.text(string, x, y, col)
        self.show()
        
    def clear(self):
        self.fill(0)
        self.show()
    
    def hw_scroll_off(self):
        self.write_cmd(SET_HWSCROLL_OFF) # turn off scroll
        
    def hw_scroll_h(self, direction=True):   # default to scroll right
        self.write_cmd(SET_HWSCROLL_OFF)  # turn off hardware scroll per SSD1306 datasheet
        if not direction:
            self.write_cmd(SET_HWSCROLL_LEFT)
            self.write_cmd(0x00) # dummy byte
            self.write_cmd(0x07) # start page = page 7
            self.write_cmd(0x00) # frequency = 5 frames
            self.write_cmd(0x00) # end page = page 0
        else:
            self.write_cmd(SET_HWSCROLL_RIGHT)
            self.write_cmd(0x00) # dummy byte
            self.write_cmd(0x00) # start page = page 0
            self.write_cmd(0x00) # frequency = 5 frames
            self.write_cmd(0x07) # end page = page 7
            
        self.write_cmd(0x00)
        self.write_cmd(0xff)
        self.write_cmd(SET_HWSCROLL_ON) # activate scroll
        
    #---------------------------------------#  
    #画垂直直线                      
    #framebuf.vline(x,y,w,c) 
    #---------------------------------------#  
    #画水平直线            
    #framebuf.hline(x,y,w,c)
    #---------------------------------------#
    #画直线,可以是斜的
    #framebuf.line(x1,y1,x2,y2,c) 
    #---------------------------------------#
    #画空心矩形
    #framebuf.rect(x,y,w,h,c)
    #举例oled.rect(0,0,8,4,1)
    #---------------------------------------#            
    #画填充矩形
    #framebuf.fill_rect(x,y,w,h,c)
    #---------------------------------------#
    #画矩形函数
    #fill为是否填充，默认不填充
    def Draw_rect(x0,y0,x1,y1,color=1,fill=0):
        if (fill==1):
            for i in range(y1-y0):
                self.framebuf.hline(x0,y0+i,x1-x0,color)
        else:
            self.hline(x0,y0,x1-x0,color)
            self.hline(x0,y1,x1-x0,color)
            self.vline(x0,y0,y1-y0,color)
            self.vline(x1,y0,y1-y0,color)
    
    #draw_chinese(self, ch_str, x_axis, yaxis)可以显示16*16的汉字和16*8的英文
    #x_axis,y_axis分别是 字符串在x方向偏移的英文宽度，y方向上偏移的汉字和英文高度
    def draw_chinese(self, ch_str, x_axis, y_axis):
        offset_ = 0
        y_axis = y_axis * 16 #  中文高度一行占8个
        x_axis = x_axis * 8  # 中文宽度占16个 
        for k in ch_str:
            code = 0x00  # 将中文转成16进制编码
            data_code = k.encode("utf-8")
            if len(data_code) >= 2:
                code |= data_code[0] << 16
                code |= data_code[1] << 8
                code |= data_code[2]
                #取font文件里byte2的文件
                byte_data = font.byte2[code]
                for y in range(0, 16):
                    a_ = bin(byte_data[y]).replace('0b', '')
                    while len(a_) < 8:
                        a_ = '0' + a_
                    b_ = bin(byte_data[y + 16]).replace('0b', '')
                    while len(b_) < 8:
                        b_ = '0' + b_
                    for x in range(0, 8):
                        self.pixel(x_axis + x + offset_, y + y_axis, int(a_[x]))  # 文字的上左半部分
                        self.pixel(x_axis + x + 8 + offset_, y + y_axis, int(b_[x]))  # 文字的右半部分
                offset_ += 16
            else:
                code = data_code[0]
                byte_data = font.byte[code]
                for y in range(0, 16):
                    a_ = bin(byte_data[y]).replace('0b', '')
                    while len(a_) < 8:
                        a_ = '0' + a_
                    for x in range(0, 8):
                        self.pixel(x_axis + x + offset_, y + y_axis, int(a_[x]))
                offset_ += 8
    #draw_all(self, it_id, x_size, y_size, x_axis, yaxis)可以显示一个大小为x_size*y_size左上角在（x_axis，y_axis）的图像。
    # it_id是这个图像在font.py中byte3字典的键
    def draw_all(self, it_id, x_size, y_size, x_axis, y_axis):
        byte_data = font.byte3[it_id]
        for times in range(0,-(-x_size//8)):
            for y in range(0, y_size):
                a_ = bin(byte_data[y+y_size*times]).replace('0b', '')
                while len(a_) < 8:
                    a_ = '0' + a_
                for x in range(0, 8):
                    self.pixel(x_axis + x + 8*times, y + y_axis, int(a_[x]))

    def read_flash_display(spi=2, cs=26,oled_cs=Pin(15)):
        #print("SPI flash")
        cs = Pin(cs, Pin.OUT, pull=Pin.PULL_UP)
        spi = SPI(spi, baudrate=4200000, polarity=0, phase=0)

        flash = SPIFlash(spi, cs,oled_cs)
        oled_cs.value(0)
        cs.value(1)
        flash.wait()
        '''
        print("Getting chip ID...")
        flash.wait()
        id_ = flash.getid()
        print("ID:", ubinascii.hexlify(id_))

        print("Reading block (32b) from address 0...")
        buf = bytearray(32*8)
        flash.read_block(0, buf)
        print(ubinascii.hexlify(buf))
        '''
        # Address= ((MSB - 0xA1) * 94 + (LSB - 0xA1))*32+BaseAdd; 
        #啊国标码b0a1,计算结果=(b0-a1 )* 94
        #啊对应区位码：1601　国标码：B0A1
        #区位码是四位的十进制数字，是GB2312国标码中的分区表示方法，区位码的前两位数是“区号”，后两位数是“位号”。区号和位号分别加上160，再分别转换成十六进制数，就成为四位的十六进制GB2312国家标准编码（简称国标码）
        GBCode=0xB0A1
        GBCode_MSB        = (GBCode >> 8) & 0xFF    #汉字内码的高八位
        GBCode_LSB        = GBCode & 0xFF          #汉字内码的低八位
        #计算地址，见手册《GT20L16S1Y用户手册》
        BaseAddr=0x00
        if(GBCode_MSB == 0xA9 and GBCode_LSB >= 0xA1):       
            WordAddr  = (282+(GBCode_LSB-0xA1))*32+ BaseAddr
            
        elif (GBCode_MSB >= 0xA1 and GBCode_MSB <= 0xA3 and GBCode_LSB >= 0xA1):        
            WordAddr = (GBCode_MSB-0xA1)*94+(GBCode_LSB-0xA1)*32+ BaseAddr
        #汉字  
        elif (GBCode_MSB >= 0xB0 and GBCode_MSB <= 0xF7 and GBCode_LSB >= 0xA1):        
            WordAddr  = ((GBCode_MSB-0xB0)*94+(GBCode_LSB-0xA1)+846)*32+ BaseAddr
        
        addr =WordAddr
        #addr = 15 * 94
        print("Reading block (32b) from address {}...".format(addr))
        flash.read_block(addr, buf)
        #print(ubinascii.hexlify(buf))
        offset_ = 0
        y_axis = y_axis * 16 #  中文高度一行占8个
        x_axis = x_axis * 8  # 中文宽度占16个 
        #取font文件里byte2的文件
        byte_data = flash.read_block(addr, buf)
        oled_cs.value(1)
        for y in range(0, 16):
            a_ = bin(byte_data[y]).replace('0b', '')
            while len(a_) < 8:
                a_ = '0' + a_
            b_ = bin(byte_data[y + 16]).replace('0b', '')
            while len(b_) < 8:
                b_ = '0' + b_
            for x in range(0, 8):
                self.pixel(x_axis + x + offset_, y + y_axis, int(a_[x]))  # 文字的上左半部分
                self.pixel(x_axis + x + 8 + offset_, y + y_axis, int(b_[x]))  # 文字的右半部分
        offset_ += 16


        """     
        #hardware scroll demo
        #https://github.com/timotet/SSD1306     
         # scroll right
        display.hw_scroll_h()
        time.sleep(3)

        # scroll left
        display.hw_scroll_h(False)
        time.sleep(3)
        
       #scroll off
        display.hw_scroll_off()
        time.sleep(3)
      
        display.clear()
        time.sleep(1)
        """      
        
    """    
    # This is for the diagonal scroll, it shows wierd actifacts on the lcd!!  
    def hw_scroll_diag(self, direction=True):   # default to scroll verticle and right
        self.write_cmd(SET_HWSCROLL_OFF)  # turn off hardware scroll per SSD1306 datasheet
        if not direction:
            self.write_cmd(SET_HWSCROLL_VL)
            self.write_cmd(0x00) # dummy byte
            self.write_cmd(0x07) # start page = page 7
            self.write_cmd(0x00) # frequency = 5 frames

            self.write_cmd(0x00) # end page = page 0
            self.write_cmd(self.height)
        else:
            self.write_cmd(SET_HWSCROLL_VR)
            self.write_cmd(0x00) # dummy byte
            self.write_cmd(0x00) # start page = page 0
            self.write_cmd(0x00) # frequency = 5 frames
            self.write_cmd(0x07) # end page = page 7
            self.write_cmd(self.height)
            
        self.write_cmd(0x00)
        self.write_cmd(0xff)
        self.write_cmd(SET_HWSCROLL_ON) # activate scroll
    """




    #该函数为字符以及字符串显示的核心部分，函数中chr=chr-' '
    #这句是要得到在字符点阵数据里面的实际地址，因为我们的取模是从空格键开始的，
    #例如oled_asc2_1206[0][0]，代表的是空格符开始的点阵码。
    #在接下来的代码，我们也是按照从上到小，从左到右的取模方式来编写的.
    #先得到最高位，然后判断是写1还是0，画点；
    #接着读第二位，如此循环，直到一个字符的点阵全部取完为止。
    #这其中涉及到列地址和行地址的自增，根据取模方式来理解，就不难了。
    def OLED_ShowChar(self, x, y, chr, size, mode):                      
        y0=y
        #得到字体一个字符对应点阵集所占的字节数 
        if size%8:  #如果大于等于8
            csize=(size/8+1)*(size/2)
        else: 
            csize=(size/8)*(size/2)
        chr=chr-' '  #得到偏移后的值,即减去空格
        for t in range(csize):
            if(size==12):
                temp=asc2_1206[chr][t]   #调用1206字体
            elif(size==16):
                temp=asc2_1608[chr][t]   #调用1608字体
            elif(size==24):
                temp=asc2_2412[chr][t]   #调用2412字体
            else:
                return              #没有的字库

            for t1 in range(8): 
                if(temp&0x80):
                    self.pixel(x,y,mode) 
                else:
                    self.pixel(x,y,not mode) 
                temp<<=1
                y+=1
                if((y-y0)==size):  #换行
                    y=y0 
                    x+=1
                    break 

    #函数功能: 显示2个数字                                                  
    #入口参数：                                                            
    #                      x,y :起点坐标                                    
    #                      len :数字的位数                                  
    #                      size:字体大小                                        
    #            mode:模式   0,填充模式 1,叠加模式                            
    #            num:数值(0~4294967295)                                    
    #************************************************************************/           
    def OLED_ShowNum(self,x,y,num,len,size):           
        enshow=0
        import math
        for t in range(len):            
            temp=(num / math.pow(10,len-t-1))%10 
            if(enshow==0 and t<(len-1)):        
                if(temp==0):            
                    OLED_ShowChar(x+(size/2)*t,y,' ',size,1) 
                    continue 
                else:
                    enshow=1
            OLED_ShowChar(x+(size/2)*t,y,temp+'0',size,1)


    #函数功能: 显示字符串      !!!可能有问题,python没指针                                                                      
    #入口参数：                                                                                                                          
    #                      x,y:起点坐标                                                
    #                      size:字体大小                                                          
    #                      *p:字符串起始地址                                                                
    #***********************************************************************
    def OLED_ShowString(self, x, y,  p, size): 
        while((p<='~') and (p>=' ')): #判断是不是非法字符!       
            if(x>(128-(size/2))):
                x=0
                y+=size 
            if(y>(64-size)):
                y=x=0
                OLED_Clear() 
            OLED_ShowChar(x,y,p,size,1)     
            x+=size/2 
            p+=1


class SSD1306_I2C(SSD1306):
    def __init__(self, width, height, i2c, addr=0x3c, external_vcc=False):
        self.i2c = i2c
        self.addr = addr
        self.temp = bytearray(2)
        self.write_list = [b'\x40', None] # Co=0, D/C#=1
        super().__init__(width, height, external_vcc)

    def write_cmd(self, cmd):
        self.temp[0] = 0x80 # Co=1, D/C#=0
        self.temp[1] = cmd
        self.i2c.writeto(self.addr, self.temp)

    def write_data(self, buf):
        self.write_list[1] = buf
        self.i2c.writevto(self.addr, self.write_list)

class SSD1306_SPI(SSD1306):
    def __init__(self, width, height, spi, dc, res, cs, external_vcc=False):
        self.rate = 10 * 1024 * 1024
        dc.init(dc.OUT, value=0)
        res.init(res.OUT, value=0)
        cs.init(cs.OUT, value=1)
        self.spi = spi
        self.dc = dc
        self.res = res
        self.cs = cs
        import time
        self.res(1)
        time.sleep_ms(1)
        self.res(0)
        time.sleep_ms(10)
        self.res(1)
        super().__init__(width, height, external_vcc)

    def write_cmd(self, cmd):
        self.spi.init(baudrate=self.rate, polarity=0, phase=0)
        self.cs(1)
        self.dc(0)
        self.cs(0)
        self.spi.write(bytearray([cmd]))
        self.cs(1)

    def write_data(self, buf):
        self.spi.init(baudrate=self.rate, polarity=0, phase=0)
        self.cs(1)
        self.dc(1)
        self.cs(0)
        self.spi.write(buf)
        self.cs(1)

