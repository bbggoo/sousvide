# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)
import network
import time
import ntptime 
from machine import RTC
from machine import Pin, SPI
from format_str_pro import ssd1306_spi_lump_print_str
from sh1106 import SH1106_SPI
#中文字体
import font
#蓝色灯
LED = Pin(2,Pin.OUT)
ssid= 'AP'
password= '88888888'
#oled实例化#3为空引脚，
spi = SPI(2,baudrate=8000000, polarity=0, phase=0, sck=Pin(14), mosi=Pin(13), miso=Pin(12))
oled = SH1106_SPI(128, 64, spi, dc=Pin(25), res=Pin(16), cs=Pin(15))

def display_logo():
    '''
     OLED显示logo
    '''
    oled.fill(0)                  #清屏
    #oled.draw_all(0x01,128,64,0,0)
    oled.show()
    time.sleep(1.1)

def display_connecting():
    '''
     OLED显示连接信息
    '''
    oled.fill(0)                  #清屏
    oled.draw_chinese('连接网络',0,0)
    #oled.text('Connecting:' + ssid,2,2)
    oled.text(ssid,20,32)
    oled.show()
def display_connected():
    '''
     OLED显示连接失败
    '''
    oled.fill(0)                  #清屏
    oled.text('ssid '+ ssid +' Connected',2,28)
    oled.show()

def display_connect_fail():
    '''
     OLED显示连接失败
    '''
    oled.fill(0)                  #清屏
    oled.text('Connect ' + ssid +' failed',2,28)
    oled.show()
    
def display_sync_fail():
    '''
     OLED显示连接失败
    '''
    oled.fill(0)                  #清屏
    oled.text('Time sync failed',2,28)
    oled.show()
    time.sleep(1)

def display_ip():
    '''
     OLED显示IP
    '''
    oled.fill(0)                  #清屏
    oled.text('IP ADDRESS:',0,4)
    oled.text(wlan.ifconfig()[0],4,26)
    oled.show()
    time.sleep(0.7)
    
display_logo()
    
#根据设定连接网络
count = 0
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
if not wlan.isconnected():
    print('connecting to TurnipSmart...')
    display_connecting()
    wlan.connect(ssid,password)
    while not wlan.isconnected() and count < 20:
        LED.value(not LED.value())
        count += 1
        time.sleep(0.5)
if wlan.isconnected(): 
    LED.value(0)
    print('IP ADDRESS: ',wlan.ifconfig()[0])
    display_connected()
else:
    LED.value(1)
    print('TurnipSmart connect fail')
    display_connect_fail()
    time.sleep(1)

def NetTimeSync():
     try:
          ntptime.settime()  # Synchronise the system time using NTP

     except Exception as e: 
          print('NTP server connection failed,please reboot board!') 	
          print("Couldn't parse")
          print('Reason:', e)

     else:
          TIMEZONE_OFFSET=8 #+8，time zone，beijing ，taipei
          (year, month, mday, week_of_year, hour, minute, second, milisecond)=RTC().datetime()
          #设定RTC时间,RTC不能在运行中更新，否则可能影响程序运行（utime）
          RTC().init((year, month, mday, week_of_year, hour+TIMEZONE_OFFSET, minute, second, milisecond)) # GMT correction. GMT+8,第8区时间
          print ("Fecha/Hora (year, month, mday, week of year, hour, minute, second, milisecond):", RTC().datetime())
          #print ("{:02d}/{:02d}/{} {:02d}:{:02d}:{:02d}".format(RTC().datetime()[2],RTC().datetime()[1],RTC().datetime()[0],RTC().datetime()[4],RTC().datetime()[5],RTC().datetime()))          

#液晶屏显示时间，时间源RTC
def show_time():
#为了美观，个位数的分钟、秒钟要加0
   if RTC().datetime()[5] < 10:  #分钟
        tMin=str( "%02d" % RTC().datetime()[5])
    #  tMin=str(RTC().datetime()[5]).zfill(2)
   else:
        tMin=str(RTC().datetime()[5])
   if RTC().datetime()[6] < 10: #秒钟
        tSec=str("%02d" % RTC().datetime()[6])
     #tSec=str(RTC().datetime()[6]).zfill(2) 
   else:
        tSec=str(RTC().datetime()[6])
   tNow =str(RTC().datetime()[4])+str(':')+tMin+str(':')+tSec #数字必须转换为文本类型,python是强类型转换
   #print(RTC().datetime()[5])
   #print(tNow)
   oled.fill(0)  #清屏
   oled.text(tNow,0,0)
   oled.show() # 显示当前时间，时:分,从（0.0）位置开始

#判断是否需要同步时间，以免同步失败浪费时间，同时显示时间
def UpdateTime():
     try:
          if( (time.localtime()[4]==RTC().datetime()[5]) and (time.localtime()[3]==RTC().datetime()[4]) and (time.localtime()[5]-RTC().datetime()[6])<=3):
               print("同步前本地时间：%s" %str(time.localtime()))
               NetTimeSync()
               time.sleep(1)
          #(year, month, mday, hour, minute, second, weekday, yearday)=utime.localtime()
     except Exception as e: 
          print('NTP server connection failed,please reboot board!') 	
          print("Couldn't parse")
          print('Reason:', e)
          display_sync_fail()
     else:
          #判断时，分相同，秒差3秒只内不同步，否则同步,目前只考虑rtc秒低于Internet
               print(" 同步后本地时间：%s" %str(time.localtime()))
               #show_time()
               

display_ip()
#time.sleep(2)
UpdateTime()
