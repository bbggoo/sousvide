
#开机wif就已经连接
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
# MISO                   19                  –主设备数据输入，从设备数据输出/与fso共用
# DC                     16                   选择指令或数据 (u8g配置中的A0)
# CS1                    5                  屏幕片选
# FSO                    19                  字库输出
# CS2                    2                   字库片选

from machine import Pin, SPI, I2C,RTC
from machine import Timer, PWM #定时器

import utime as time
from utime import sleep_us, sleep_ms
#读写配置文件
import json

import network
import socket ##send data to  web server

from rtd import rtd #max38615
from pid import PIDArduino

from sh1106 import SH1106_SPI
#from format_str_pro import ssd1306_spi_lump_print_str
#中文字体
import font


##旋转编码器
import time
from rotary_irq_esp import RotaryIRQ
'''
rotary = RotaryIRQ(pin_num_clk=36, 
              pin_num_dt=39, 
              min_val=0, 
              max_val=9, 
              reverse=False, 
              range_mode=RotaryIRQ.RANGE_WRAP)
'''
import uasyncio as asyncio
from primitives.switch import Switch
from primitives.pushbutton import Pushbutton
#import uasyncio
import gc
import array #数组，给温度用
import math
import logging
logging.basicConfig(level=logging.INFO)

cancel_pin = Pin(33, Pin.IN, Pin.PULL_UP)
cancel_sw = Switch(cancel_pin)          
start_pin = Pin(32, Pin.IN, Pin.PULL_UP)    
start_sw = Switch(start_pin)
timer_pin = Pin(21, Pin.IN, Pin.PULL_UP)    
timer_sw = Switch(timer_pin)
temp_pin = Pin(22, Pin.IN, Pin.PULL_UP)    
temp_sw = Switch(temp_pin)
menu_pin = Pin(4, Pin.IN, Pin.PULL_UP)    
menu_sw = Switch(menu_pin) 
#旋转编码器按钮
rotary_btn_pin = Pin(34, Pin.IN, Pin.PULL_UP)    
rotary_sw = Switch(rotary_btn_pin)
#旋转编码器按钮按动次数计数器
rotary_press_count=0
#旋转编码器
rotary = RotaryIRQ(pin_num_clk=36, 
            pin_num_dt=39, 
            min_val=0, 
            max_val=9, 
            reverse=False, 
            range_mode=RotaryIRQ.RANGE_WRAP)

#initial spi oled，miso与字库共用，都写成gpio 19。 res没引出，设为3，否则oled实例化失败
spi = SPI(2,baudrate=8000000, polarity=0, phase=0, sck=Pin(14), mosi=Pin(13), miso=Pin(12))
oled = SH1106_SPI(128, 64, spi, dc=Pin(25), res=Pin(16), cs=Pin(15))


#显示中文
#oled.draw_chinese('我',0,0)
#oled.draw_chinese('我',4,2)
wlan = network.WLAN(network.STA_IF)

is_heating = 0 # State heating in oled,io output,when heating set to 1
is_setpoint_flag=0
is_countdown_flag=0
# PWM Control,设定输出引脚，频率，占空比
heater = PWM(Pin(27)) #GPIO 27
heater.freq(1)
#默认占空比0
heater.duty(0)
#PID Setup

#下面是自由变量，由于没定义系统会报错，所以要先定义并赋值
#参数初始化，p、i、d分别是pid参数
p = '0.00'
i = '0.00'
d = '0.00'
#duty占空比，大部分情况下drive=duty
#drive是计算出来，考虑了最大值和最小值后的值
drive='0.0'
duty='0'
duty_min=str('0')
duty_max=str('1023')
#控制周期，经过测试，15.5秒上升1摄氏度，1.5秒上升0.1摄氏度，如果允许误差0.2度，应该设置3秒
sleep_time =str('1.0')  #Control loop interval (seconds)
# sleep_time 采样时间， kp, ki, kd，输出最小值，输出最大值，时间
#Create simple PID object with saturation value of 1023
#PID = PIDArduino(sleep_time,p,i,d,duty_min,duty_max) 
#www服务器的ip
#设定加热时间计时器,从达到目标温度并按下开始按钮后计算，单位分钟,所以要乘以60,变成秒,因为时间戳的单位是秒的浮点数
countdown_timer='7200'            #str('120*60')
#先定义开始时间,为进入程序的时间,剩余时间为倒计时时间=加热时间计时器-(当前时间-进入程序的时间)
#start_time=float('0')
#time_left=float('0')
#设置目标温度。单位摄氏度，要转换成文本
setpoint=str('57.2') 
#temp为传感器读出的数据
temp =str('0')
webhost=str('10.0.0.117')

wifi_linked=1 #State wifi_linked in oled
#rotary_btn = Pin(34) # enc button, gpio in esp32

__author__ = 'stategrid'
# modified from author StoryMonster
#https://blog.csdn.net/StoryMonster/article/details/99443480?utm_medium=distribute.pc_relevant.none-task-blog-baidujs-1
'''
SousVide控制器的5种状态：
    1.长加热,加热灯亮,长按停止进入空闲状态,到达目标温度时告警,一直往外发送数据
    按加热进入倒计时状态,否则一直加热并发出告警.
    
    
    2.空闲,显示当前时间,加热灯灭,隔一段时间蜂鸣一次
    按加热进入加热状态(已经预设定目标温度,目标时间),
    按加热健进入设置温度状态,
    按设置目标时间,则进入定时状态.
    
    3. FsmFinalState,保存定时和设置温度初始设置,下次开机直接调用
    
    4.定时,按取消返回空闲状态,按确定存储定时数据并返回空闲状态,
    
    5.设置温度,按取消返回,按确定存储目标温度数据并返回空闲状态,
    
    6.倒计时状态,到达设定时间后停止加热并告警,进入空闲状态.
    一直往外发送数据
    按取消健进入空闲状态
       
'''

def read_config():
    #  将文件中的内容读取并加载到字典变量 config
    global setpoint,countdown_timer,webhost
    with open('sys_config.json','r') as f:
        config = json.loads(f.read())

        setpoint=config['spt']
        countdown_timer=config['cdn_timer']
        webhost=config['host']
def write_config(): 
    global setpoint,countdown_timer,webhost
    #  执行配置文件config的创建 
    #print('begin to writeconfig:')
    spt=setpoint
    cdn_timer='7200' ##second
    host='10.0.0.117'
    config = dict(spt=setpoint, cdn_timer=countdown_timer,host=webhost) # 创建字典
    with open('sys_config.json','w') as f:
        f.write(json.dumps(config)) # 将字典序列化为json字符串,存入sys_config.json

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
   oled.text('CLOCK',0,4)
   oled.text(tNow,22,32)
   oled.show() # 显示当前时间，时:分,从（0.0）位置开始

#加热时显示温度
async def show_temp():
    global error ,setpoint,temp
    #读取温度设定
    read_config()
    oled.fill(0)                  #清屏
    #oled.text('CURRENT TEMPERATURE',0,0)
    oled.draw_chinese('当前温度',0,0)
    oled.text(str("{:.2f}".format(float(temp))),2,18)
    oled.text('>>>',104,18)
    #白色线,1
    oled.hline( 0, 30, 128, 1)
    #oled.text('TARGET TEMPERATURE',0,36)
    #每个占16高度,最大64/16=4
    oled.draw_chinese('既定温度',0,2)
    oled.text(str(setpoint),4,52)
    oled.show()
    await asyncio.sleep_ms(400)

def count_add():
    global rotary_press_count
    rotary_press_count=rotary_press_count+1
    print("rotary_press_count is:",rotary_press_count)

#async def sleep_time():
#    await asyncio.sleep(50)     
    
#显示设置温度界面
async def show_countdown():
    global m_total 
    h, m = divmod(m_total, 60)  # 获取小时，分 
    oled.fill(0)     #清屏   
    oled.draw_chinese('剩余时间',0,0)
    oled.draw_chinese('当前温度',0,2)
    oled.text(str("{:.2f}".format(temp)),68,38) 
    #白色线
    oled.hline( 0, 26, 128, 1)
    #m_total类型为float 
    #oled.text(str(m_total),0,40)
    if h>0:
        #不带小数点
        oled.text(str("{:.0f}".format(h)),66,6)
        #oled.text(' Hour',4,35)
        oled.draw_chinese('时',9,0)
        oled.text(str("{:.0f}".format(m)),94,6)
        oled.draw_chinese('分',14,0)
        #oled.text(' Min',70,35)

    else:
        oled.text(str("{:.0f}".format(m)),56,35)
        #oled.text(' Min',70,35)
        oled.draw_chinese('分',14,2) 
        #print('h =0')
    oled.show() #显示温度              
    await asyncio.sleep_ms(10000)


#发送数据到url
def http_get(url):
    #split()：拆分字符串。
    # 通过指定分隔符对字符串进行切片，分割3次，并返回分割后的字符串列表（list），从0开始
    #path结果为PID开头的字符串
    #前面两个是私有参数？还是0-1，后面是字符串列表的2-3
    _, _, host, path = url.split('/', 3)
    #print(str(host))
    #这里sockaddr 是一个 (address, port) 二元组
    #获取首个有效地址和服务端的IP地址和端口
    addr = socket.getaddrinfo(host, 80)[0][-1]
    #print( "addr is: " & addr )
    s = socket.socket()
    try:
        s.connect(addr)
    except:
        pass
        #raise
    else:
        #换行符是\r\n
        s.send(bytes('GET /%s HTTP/1.0\r\nHost: %s\r\n\r\n' % (path, host), 'utf8'))
        while True:
            data = s.recv(200)
            if data:
                #print(str(data, 'utf8'), end='')
                break
            else:
                break
        s.close()


#获取温度
def get_temp():
    global temp
    try:
        temp =str(rtd.temperature)
    except:
        #If sensor read fails, use a sentinel value so control loop continues but the error is obvious on the graph
        #To fail SAFE the sentinel value must be higher than the setpoint, so that the heater is gradually turned off with failed reads
        temp = 123.45
    return temp

def pressbreak():
    while true:
        break

#后续考虑变化率来提高精度
#这个是温度差与目标温度的比率
#esIndex=error/setpoint
async def process():
    #分段进行pid
    global error ,setpoint,temp,sleep_time,p,i,d,duty_min,duty_max
    #try:
    #当前温度，由于显示需要，默认为文本类型
    temp =get_temp()
    #当前温度和目标的差值
    error =float(setpoint) - float(temp)
    
    #error =setpoint - temp
    #如error<3 key=1
    if error>1.8 :
        p =260.1905290193251004
        i = 0
        d = 0.00000000000001
        #continue
    #print('strategy结果为:', strategy )
    elif error <= 1.8 and error >= 0.2:
        p = 1200.1905290193251004
        i =80
        d = 00.0011112
        #continue
    elif error < 0.2 and error >= 0.05:
        p = 1250.1905290193251004
        i = 168.58
        d = 00.0000932
        #倒开始计时
        #count_down(countdown_timer)
    else:
    #清除
        p = 1250.442732409779707
        i = 182.200001
        d = 0.000000001
        #duty_min=32
        
    p=float(p)
    i=float(i)
    d=float(d)
    sleep_time=float(sleep_time)
    duty_min=float(duty_min)
    duty_max=float(duty_max)
    # 采样时间， kp, ki, kd，输出最小值，输出最大值，时间
    PID = PIDArduino(sleep_time,p,i,d,duty_min,duty_max)
    print('{0:>10}{1:>10}{2:>10}{3:>7}{4:>10}{5:>10}{6:>10}'.format('TEMP', 'ERROR', 'DRIVE', 'DUTY', 'P', 'I', 'D'))
    #temp = float(get_temp())
    #error = setpoint - temp
    setpoint=float(setpoint)
    temp=float(temp)
    drive = PID.calc(temp,setpoint)
    #占空比，下面这里是大于最小值，小于最大值，这里设定为0，1023
    #duty =1024和max(int(drive),0)两者中小的。int (drive),中两者大的
    duty = min(max(int(drive),0),1023)
    #print("duty:",duty)
    #通过位置来填充字符串,并按参数格式化
    print('{temp:10.3f}{error:10.3f}{drive:10.2f}{duty:7}{p:10.2f}{i:10.2f}{d:10.2f}'.format(temp=temp, error=error, drive=drive, duty=duty, p=p, i=i, d=d))
    heater.duty(duty)
    #通过位置来填充字符串
    url = 'http://'+ webhost + '/PIDStoreZQ3jHPDy85.php?temp={}&error={}&duty={}&p={}&i={}&d={}'.format(str(temp), str(error), str(duty), str(p), str(i), str(d))
    http_get(url)
    await asyncio.sleep_ms(int(sleep_time))    
    #time.sleep(sleep_time)

class FsmState:
    def enter(self, event, fsm):  ## 参数event为触发状态转换的事件, fsm则为状态所在状态机
        pass
    
    def exit(self, fsm):
        pass
#开机,进入初始状态
class power_on(FsmState):
    def enter(self, event, fsm):
        print("sousvide is power on")
        show_time()

#加热状态
class heating(FsmState):       
    def enter(self, event, fsm):
        global error ,setpoint,temp,sleep_time,p,i,d,duty_min,duty_max,is_setpoint_flag,cancel_sw,show_task,pro_task
        print("sousvide begin heating")
        while True:
            #process()
            #show_temp()
            if( (float(setpoint)-float(temp))<0.1):
                is_setpoint_flag=1     
                #cancel_sw.close_func(pressbreak)
            show_task = asyncio.run(show_temp())            
            pro_task = asyncio.run(process())
                  
    def exit(self, fsm):
        print("sousvide stoped heating")
        global show_task,pro_task
        #show_task.cancel()
        #pro_task.cancel()

class countdown(FsmState):       
    def enter(self, event, fsm):
        global error ,setpoint,temp,countdown_timer,cancel_sw,start_time ,time_left ,m_total,is_countdown_flag
        print("sousvide is going to count down")
        #程序开始时间        
        start_time = time.time()   #计时精度够了  
        oled.fill(0)                  #清屏
        oled.draw_chinese('倒计时',0,0)
        #oled.text(str(countdown_timer/60)+' Min',0,40)
        #白色线
        #oled.hline( 0, 32, 128, 1)
        oled.show()
        while True:       
            # 加热
            #global error ,setpoint,temp,countdown_timer,cancel_sw,start_time 
            #nonlocal time_left
            #countdown_timer   # 计时设定时间
            #time_left   # 剩余时间,单位是浮点秒数 
            t1 = time.time() - start_time  # 计时时间间隔,单位秒
            #countdown_timer类型为str,要转换
            time_left = float(countdown_timer) - t1  # 剩余时间
            m_total, s = divmod(time_left, 60)  # 获取分， 秒
            h, m = divmod(m_total, 60)  # 获取小时，分            
          
            if time_left > 0:
                # print("%02d:%02d:%02d" % (h, m, s))  正常打印
                #加热
                #process()
               pro = asyncio.run(process())
                # 显示剩余加热时间  
               show = asyncio.run(show_countdown())                        
                #print("\n\r%02d:%02d:%02d\n" % (h, m, s),end="")  # 每次把光标定位到行首，打印
                
            else:
                print("\n计时结束")
                is_countdown_flag=1
                #break
                #return
#'''
            # TODO 如果添加暂停/开始功能，需要做的工作
            #  1、暂停时更新 countdown_timer = time_left
            #  2、开始时更新 start_time
            #  PS: divmod()函数用法 https://www.runoob.com/python/python-func-divmod.html        
    
    def exit(self, fsm):
        print("sousvide stopped count down") 
        pro.cancel()
        show.cancel()

async def rotary_change_temp():
    global rotary,rotary_sw,rotary_press_count,val_old,val_new,setpoint,arr,new_setpoint    
    rotary = RotaryIRQ(pin_num_clk=36, 
                pin_num_dt=39, 
                min_val=0, 
                max_val=9, 
                reverse=False, 
                range_mode=RotaryIRQ.RANGE_WRAP)
    
    val_old = rotary.value()    
    rotary_press_count=0
    oled.fill(0)  #清屏         
    oled.draw_chinese('新定温度',0,0)
    #白色线,1
    oled.hline( 0, 30, 128, 1)
    #每个占16高度,最大64/16=4
    oled.draw_chinese('原定温度',0,2)
    oled.text(str("{:.2f}".format(float(setpoint))),70,40)          
    #oled.text('.',86,6) 
    #import framebuf
    #buffer = bytearray(34 * 22 // 8)        #开辟56*8像素空间
    #framebufnew = framebuf.FrameBuffer(buffer, 34, 22, framebuf.MVLSB) #创建新的framebuffer对象
       
    while True:
        val_new = rotary.value()
        #如果旋转编码器按钮被按下，计数器加1
        rotary_sw.close_func(count_add)
        if val_old != val_new:

             #清屏 
            #arr用来存储setpoint的高位,低位,小数点后的位数 
            #asyncio.run(sleep_time())
            #最高设置温度99.9.最低0.0
            #计数,如果按动次数被3除余数0,光标在十位数,修改该位数值,下同
            if rotary_press_count%3==0:
                #把矩形区域充0,先用oled.fill(0) 代替
                #消除三角形
                '''
                oled.draw_all(0x03,8,8,70,16)
                oled.draw_all(0x03,8,8,78,16)
                oled.draw_all(0x03,8,8,94,16)
                '''
                #framebufnew.fill(0)  #清屏
                #oled.draw_all(0x04,32,18,70,16)     
                oled.draw_all(0x02,8,8,70,16)            
                #val_new旋转编码器读数
                arr[0]=val_new
                
            #计数,如果按动次数被3除余数1,光标在个位数
            elif rotary_press_count%3==1:
                '''
                oled.draw_all(0x03,8,8,70,16)
                oled.draw_all(0x03,8,8,78,16)
                oled.draw_all(0x03,8,8,94,16)
                oled.draw_all(0x03,8,8,78,6)
                oled.draw_all(0x02,8,8,78,16)
                '''
                #framebufnew.fill(0)  #清屏
                oled.draw_all(0x04,32,18,70,16)     
                oled.draw_all(0x02,8,8,78,16)            
                arr[1]=val_new
                
            #计数,如果按动次数被3除余数2,光标在小数点后第一位
            elif rotary_press_count%3==2:
                '''
                #清除
                oled.draw_all(0x03,8,8,70,16)
                oled.draw_all(0x03,8,8,78,16)
                oled.draw_all(0x03,8,8,94,16)
                oled.draw_all(0x03,8,8,94,6)
                oled.draw_all(0x02,8,8,94,16)
                '''
                #framebufnew.fill(0)  #清屏
                oled.draw_all(0x04,32,18,70,16)    
                oled.draw_all(0x02,8,8,94,16)             
                arr[2]=val_new
            val_old = val_new

        #setpoint=arr[0]*10+arr[1]+arr[2]*0.1
        '''
        framebufnew.text(str(arr[0]), 0, 0)      #新的framebuffer输入字符串
        framebufnew.text(str(arr[1]), 8, 0)
        framebufnew.text('.',16,0) 
        framebufnew.text(str(arr[2]), 24, 0)
        oled.blit(framebufnew, 70, 6)           #新的frambuffer起始坐标
        '''
        oled.text(str(arr[0]),70,6)
        oled.text(str(arr[1]),78,6)
        oled.text(str(arr[2]),94,6)
        oled.text('.',86,6)
        #'''
        oled.show()
        await asyncio.sleep_ms(800)

#设置温度
class set_temp(FsmState):           
    def enter(self, event, fsm):
        #加上打开json语句
        print("sousvide setting temperature")
        #
        global rotary,rotary_sw,rotary_press_count,val_old,val_new,setpoint,arr,new_setpoint
        #读取温度设定
        read_config()
        setpoint= float(setpoint)
        #xs 小数点后，会有误差
        #zs整数
        xs,zs=math.modf(setpoint)
        aa = int(zs / 10)  #十位
        bb = int(zs % 10)  #个位        
        cc=int(10*xs)#小数点后第一位
        #dd=int(100*xs)%10#小数点后第二位

        print("original num is:\n %.2f" %setpoint)
        #print("after :\n %d,%d,%d,%d" %(aa,bb,cc,dd))

        #设定数组，初始化,为了以后方便，精度可扩展到小数点后两位
        arr = array.array('b', [])
        arr.append(aa)#十位数
        arr.append(bb)#个位
        arr.append(cc)#小数点后第一位
        #arr.append(dd)#小数点后第二位 

        print("enter setting temperature") 
        asyncio.create_task(rotary_change_temp())
        #修改十位
        #修改个位
        #修改小数点后第一位
        #修改小数点后第二位
        #存在setpoint这个值

        asyncio.run(rotary_change_temp())
             
    def exit(self, fsm):
        print("sousvide stoped setting temperature")
        print('saving config')
        #保存到json
        write_config()
        
async def rotary_change_timer():
    global rotary,rotary_sw,rotary_press_count,val_old,val_new,countdown_timer,arr_t
    rotary = RotaryIRQ(pin_num_clk=36, 
                pin_num_dt=39, 
                min_val=0, 
                max_val=9, 
                reverse=False, 
                range_mode=RotaryIRQ.RANGE_WRAP)
    
    val_old = rotary.value()    
    rotary_press_count=0
    oled.fill(0)  #清屏         
    oled.draw_chinese('新定时间',0,0)
    #白色线,1
    oled.hline( 0, 30, 128, 1)
    #每个占16高度,最大64/16=4
    oled.draw_chinese('原定时间',0,2)
    oled.text(str("{:.0f}".format(float(countdown_timer))),70,40)
    oled.text('min',96,40)
    oled.text(':',78,6)
    while True:
        val_new = rotary.value()
        #如果旋转编码器按钮被按下，计数器加1
        rotary_sw.close_func(count_add)
        if val_old != val_new:
            #arr用来存储setpoint的高位,低位,小数点后的位数 
            #asyncio.run(sleep_time())
            #最高设置温度99.9.最低0.0
            #计数,如果按动次数被3除余数0,光标在十位数,修改该位数值,下同
            if rotary_press_count==0:
                #把矩形区域充0,先用oled.fill(0) 代替
                #消除三角形
                oled.draw_all(0x03,8,8,70,16)
                oled.draw_all(0x03,8,8,86,16)
                oled.draw_all(0x03,8,8,94,16)
                oled.draw_all(0x03,8,8,70,6)  
                oled.draw_all(0x02,8,8,70,16)
                #val_new旋转编码器读数
                arr_t[0]=val_new
                
            #计数,如果按动次数被3除余数1,光标在个位数
            elif rotary_press_count==1:
                oled.draw_all(0x03,8,8,70,16)
                oled.draw_all(0x03,8,8,86,16)
                oled.draw_all(0x03,8,8,94,16)
                oled.draw_all(0x03,8,8,86,6)
                oled.draw_all(0x02,8,8,86,16)
                if val_new>6:
                    val_new=0
                arr_t[1]=val_new
                
            #计数,如果按动次数被3除余数2,光标在小数点后第一位
            elif rotary_press_count==2:
                oled.draw_all(0x03,8,8,70,16)
                oled.draw_all(0x03,8,8,86,16)
                oled.draw_all(0x03,8,8,94,16)
                oled.draw_all(0x03,8,8,94,6)
                oled.draw_all(0x02,8,8,94,16)
                arr_t[2]=val_new
        if rotary_press_count==3:
            #会执行两遍,不知道原因            
            countdown_timer=arr_t[0]*60+arr_t[1]*10+arr_t[2]           
            break
            val_old = val_new
        oled.text(str(arr_t[0]),70,6)
        oled.text(str(arr_t[1]),86,6)
        oled.text(str(arr_t[2]),94,6)
        oled.show()
        await asyncio.sleep_ms(60)  
        
#定时
class set_timer(FsmState):
    def enter(self, event, fsm):  
        print("sousvide setting timer")        
        global rotary,rotary_sw,rotary_press_count,val_old,val_new,countdown_timer,arr_t
        #打开json,读取温度设定
        read_config()
        #change to minutes
        countdown_timer= int(countdown_timer)/60
        #时间格式:小时:分钟
        
        hours = int(countdown_timer/60)  #小时,最大不超过9小时
        mins = int(countdown_timer%60)  #分钟,最大不超过60
        aa = int(mins / 10)  #十位
        bb = int(mins % 10)  #个位 
        print("original num is:\n %.0f" %countdown_timer)
        #print("after :\n %d,%d,%d,%d" %(aa,bb,cc,dd))

        #设定数组，初始化,为了以后方便，精度可扩展到小数点后两位
        arr_t = array.array('b', [])
        arr_t.append(hours)#hours
        arr_t.append(aa)#mins,十位数
        arr_t.append(bb)#mins,个位
        
        print("enter setting temperature") 
        asyncio.create_task(rotary_change_timer())
        asyncio.run(rotary_change_timer())

    def exit(self, fsm):
        print("sousvide stoped setting timer")
        print('saving config')
        #保存到json
        write_config()

class menu(FsmState):
    def enter(self, event, fsm):
        print("sousvide setting menu")

    def exit(self, fsm):
        print("sousvide stoped setting menu")           
        
#定时
class link_wlan(FsmState):
    def enter(self, event, fsm):
       print("sousvide start to link wlan")
       LED = Pin(2,Pin.OUT)
       count = 0
       #while not sta_if.isconnected(): 
           # pass
       
       wlan = network.WLAN(network.STA_IF)
       wlan.active(True)
       if not wlan.isconnected():
              print('connecting to TurnipSmart...')
              wlan.connect('test','88888888')
       while not wlan.isconnected() and count <  20:
              LED.value(not LED.value())
              count += 1
              #time.sleep(0.5)
              #await asyncio.sleep_ms(500)
       if wlan.isconnected(): 
              LED.value(0)
              print('IP ADDRESS:',wlan.ifconfig()[0])
       else:
              #蓝灯闪烁
              LED.value(1)
              print('TurnipSmart connect fail') 

    def exit(self, fsm):
        print("sousvide stoped link wlan")
               
class FsmFinalState(FsmState):
    def enter(self, event, fsm):
        print("sousvide is in FsmFinalState")        

#######################################

#含有6个按钮:
#'set_temp_btn'---目标温度,
#'set_timer_btn'---定时,
#'menu_btn'--- 菜单,
#'start_btn'---开始,
#'cancel_btn'---取消,
#'link_wlan_btn'---无线连接,
#'rotary'---1个调节旋钮
#'rotary_btn'---1个调节旋钮上的按钮---
#
class FsmEvent:
    pass

class start_btn(FsmEvent):
    pass
    
class set_temp_btn(FsmEvent):
    pass

class set_timer_btn(FsmEvent):
    pass

class link_wlan_btn(FsmEvent):
    pass

class rotary_btn(FsmEvent):
    pass

class menu_btn(FsmEvent):
    pass

class cancel_btn(FsmEvent):
    pass

#到达目标温度
class setpoint_flag(FsmEvent):
    pass

#到达目标时间
class countdown_flag(FsmEvent):
    pass

class rotary(FsmEvent):
    pass

#######################################
from collections import namedtuple

Transaction = namedtuple("Transaction", ["prev_state", "event", "next_state"])    ## 一次状态转换的所有要素：上一个状态--事件-->下一个状态

class FSM:
    def __init__(self, context):                                                  ## context：状态机上下文
        self.context = context
        self.state_transaction_table = []                                         ## 常规状态转换表
        self.global_transaction_table = []                                        ## 全局状态转换表
        self.current_state = None
        self.working_state = FsmState

#issubclass(class, classinfo),如果 class 是 classinfo 的子类返回 True，否则返回 False。
    def add_global_transaction(self, event, end_state):     # 全局转换，直接进入到结束状态
        if not issubclass(end_state, FsmFinalState):
            raise FsmException("The state should be FsmFinalState")
        self.global_transaction_table.append(Transaction(self.working_state, event, end_state))

    def add_transaction(self, prev_state, event, next_state):
        if issubclass(prev_state, FsmFinalState):
            raise FsmException("It's not allowed to add transaction after Final State Node")
        self.state_transaction_table.append(Transaction(prev_state, event, next_state))

    def process_event(self, event):
        for transaction in self.global_transaction_table:
            if isinstance(event, transaction.event):
                self.current_state = transaction.next_state()
                self.current_state.enter(event, self)
                self.clear_transaction_table()
                return
            #如果不在就返回,避免出错
            if not isinstance(event, transaction.event):
                return         
         #isinstance(object, classinfo),如果对象object的类型与参数二的类型（classinfo）相同则返回 True，否则返回 False。。
        for transaction in self.state_transaction_table:
            if isinstance(self.current_state, transaction.prev_state) and isinstance(event, transaction.event):
                self.current_state.exit(self.context)
                self.current_state = transaction.next_state()
                self.current_state.enter(event, self)
                if isinstance(self.current_state, FsmFinalState):
                    self.clear_transaction_table()
                return
            #如果不在就返回,避免出错
            if isinstance(self.current_state, transaction.prev_state) and isinstance(event, transaction.event):            
                return
        pass      
        #raise FsmException("Transaction not found")
    
    def clear_transaction_table(self):
        self.global_transaction_table = []
        self.state_transaction_table = []
        self.current_state = None

    def run(self):
        if len(self.state_transaction_table) == 0: return
        self.current_state = self.state_transaction_table[0].prev_state()
        self.current_state.enter(None, self)

    def isRunning(self):
        return self.current_state is not None

    def next_state(self, event):
        for transaction in self.global_transaction_table:
            if isinstance(event, transaction.event):
                return transaction.next_state
        for transaction in self.state_transaction_table:
            if isinstance(self.current_state, transaction.prev_state) and isinstance(event, transaction.event):
                return transaction.next_state
        return None

class FsmException(Exception):
    def __init__(self, description):
        super().__init__(description)

class sousvide(FSM):
    def __init__(self):
        super().__init__(None)

if __name__ == '__main__':
    sousvide = sousvide()
    #添加转移状态图,          上一个状态--    事件  -->     下一个状态

    sousvide.add_transaction(power_on, set_timer_btn, set_timer)
    sousvide.add_transaction(power_on, set_temp_btn, set_temp)
    sousvide.add_transaction(power_on, start_btn, heating)
    sousvide.add_transaction(power_on, link_wlan_btn, link_wlan)
    
    sousvide.add_transaction(power_on, menu_btn, menu)
    sousvide.add_transaction(menu, cancel_btn,power_on) 
       
    sousvide.add_transaction(heating, cancel_btn, power_on)
    sousvide.add_transaction(heating, setpoint_flag, countdown)

    
#再次按键切换到小数点后
    sousvide.add_transaction(set_temp, set_temp_btn, set_temp)
    sousvide.add_transaction(set_temp, cancel_btn, power_on)
    
#再次按键切换到小数点后
    sousvide.add_transaction(set_timer, set_timer_btn, set_timer)
    sousvide.add_transaction(set_timer, cancel_btn, power_on)

    sousvide.add_transaction(countdown, cancel_btn, heating)
    sousvide.add_transaction(countdown, countdown_flag, FsmFinalState)

    sousvide.add_transaction(link_wlan, cancel_btn, power_on)
    sousvide.add_transaction(power_on, link_wlan_btn, link_wlan)
    
    #测试用,成功后屏蔽
    #sousvide.add_transaction(power_on, setpoint_flag, countdown)
    #sousvide.add_transaction(power_on, countdown_flag, FsmFinalState)
    #最终阶段,不能再转移了,必须重新开机
    #sousvide.add_transaction(FsmFinalState, set_timer_btn, set_timer)
    #sousvide.add_transaction(FsmFinalState, set_temp_btn, set_temp)
    #sousvide.add_transaction(FsmFinalState, start_btn, heating)
    #sousvide.add_transaction(FsmFinalState, link_wlan_btn, link_wlan)

    sousvide.run()
    #-----------------------------------------
 
    #-----------------------------------------
     
    # Quit test by connecting X2 to ground,stop?
    async def killer():
        #未引出的脚,测试
        pin = Pin(17, Pin.IN, Pin.PULL_UP)
        while pin.value():
            await asyncio.sleep_ms(50)

    def looprun():
        #try子句先执行，
        try:
            asyncio.run(killer())
            #执行时是否出现异常。
        except KeyboardInterrupt:
            print('Interrupted')
            ##退出try时总会执行
        finally:
            asyncio.new_event_loop()
            print('loop runing')

    def key_press_loop():

        print('Test of switch executing callbacks.')
    
        #pin = Pin(4, Pin.IN, Pin.PULL_UP)
        #sw = Switch(pin)
        # Register a coro to launch on contact close

        global cancel_sw,start_sw,temp_sw,menu_sw,is_setpoint_flag,is_countdown_flag
        #如果取消按钮被按下，
        cancel_sw.close_func(sousvide.process_event, (cancel_btn(),))                 
        #如果按钮被按下，
        start_sw.close_func(sousvide.process_event, (start_btn(),)) 
        #如果按钮被按下，
        timer_sw.close_func(sousvide.process_event, (set_timer_btn(),))            
        #如果按钮被按下，
        temp_sw.close_func(sousvide.process_event, (set_temp_btn(),)) 
       
        #如果按钮被按下，
        menu_sw.close_func(sousvide.process_event, (menu_btn(),))         

        #wlan_pin = Pin(?, Pin.IN, Pin.PULL_UP)    
        #wlan_sw = Switch(wlan_pin)
        #如果按钮被按下，
        #wlan_sw.close_func(sousvide.process_event, (link_wlan_btn(),)) 
        #is_setpoint_flag=1
        if is_setpoint_flag:
            sousvide.process_event(setpoint_flag())
        #is_countdown_flag=1
        if is_countdown_flag:    
            sousvide.process_event(countdown_flag())       
         
        looprun()
        
    key_press_loop()

    #sousvide.process_event(start_btn())
    #sousvide.process_event(cancel_btn())
    
    #sousvide.process_event(set_timer_btn())
    #sousvide.process_event(set_temp_btn())

    #sousvide.process_event(menu_btn())
    #sousvide.process_event(link_wlan_btn())
    
    #sousvide.process_event(setpoint_flag())
    #sousvide.process_event(countdown_flag())