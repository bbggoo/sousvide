# 1-Wire driver for MicroPython
# MIT license  Copyright (c) 2020 stategrid@gmail.com
#modified from https://docs.pycom.io/tutorials/all/owd/

import machine
from machine import Pin
from utime import sleep_us,sleep

#位运算，返回高八位，低8位
#to get HighByte,LowByte
def split(num):
    return num >> 8, num & 0xFF

class OneWireError(Exception):
    pass

class OneWire:
    def __init__(self, pin):
        self.pin = pin
        self.pin.init(pin.OPEN_DRAIN, pin.PULL_UP)

    def write_bit(self,addr):  #发送位函数。
        #发送时关掉中断，防止中断影响时序 
        state = machine.disable_irq()
        self.pin.value(1)  #开始拉高
        sleep_us(1000)
        #sleep_us( 1000 )
        self.pin.value(0)  #开始引导码 
        # minimal 2ms
        sleep_us(4000) #此处延时最少要大于2ms 
        self.pin.value(1)
        #将数字（二进制）对应位数比较，若对应位都为1，则对应位为1，否则为0；
        #即将addr按位取出
        #addr & 0x01 表示最低位,即低位在前
        #addr & 0x01 means lower bit fist
        # 3:1 time occupation means "1"    
        if ( addr & 0x01 ): #3:1表示数据位1,每个位用两个脉冲表示 
            sleep_us( 600 ) 
            self.pin.value(0)
            sleep_us( 200 )
            # 1:3  time occupation means "0"     
        else:            # 1：3表示数据位0 ,每个位用两个脉冲表示          
            sleep_us( 200 ) 
            self.pin.value(0)
            sleep_us( 600 ) 
        self.pin.value(addr)       
        self.pin.value(1)
        #恢复中断
        #resum interrupt
        machine.enable_irq(state)  
    
    def write_byte(self,addr):  #发送字节函数。
        for i in range(8):
        #总共8位数据
            self.write_bit(addr & 0x01)
            #右移运算是将一个二进制位的操作数按指定移动的位数向右移动，移出位被丢弃
            addr >>= 1 
                          
    def set_volume(self,volume):
        self.write_byte(0x0A)
        HighByte, LowByte = split(volume)
        self.write_byte(HighByte)
        self.write_byte(LowByte)
        self.write_byte(0x0C)
        sleep_us(2000)
    #play songs,track_id <15   
    def play(self,track_id):      
        self.write_byte(0x0A)
        self.write_byte(track_id)
        self.write_byte(0x0B)
        sleep_us(2200)

    def mute(self):
        self.set_volume(0)
#test code below
'''
dat = Pin(16)
#jq8400 = onewire.OneWire(dat)
jq8400 = OneWire(dat)
jq8400.set_volume(10)
jq8400.play(1) 
sleep(4)
jq8400.play(2)
'''