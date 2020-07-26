#wapm front  origin  https://hackaday.io/project/153281-super-accurate-sousvide-on-a-budget
# and https://github.com/ccspoz/sousvide
#pid control origin  https://github.com/hirschmann/pid-autotune
from machine import Pin, PWM
import time
from rtd import rtd
import socket
from pid import PIDArduino
# PWM Control,设定输出引脚，频率，占空比
heater = PWM(Pin(27)) #GPIO 27
heater.freq(1)
#默认占空比0
heater.duty(0)
#PID Setup
#目标温度
setpoint = 64.2
#下面是自由变量，由于没定义系统会报错，所以要先定义并赋值
#参数初始化，p、i、d分别是pid参数
p = 0.00
i = 0.00
d = 0.00
#duty占空比，大部分情况下drive=duty
#drive是计算出来，考虑了最大值和最小值后的值
drive='0.0'
duty=0
duty_min=0
duty_max=1023
#控制周期，经过测试，15.5秒上升1摄氏度，1.5秒上升0.1摄氏度，如果允许误差0.2度，应该设置3秒
sleep_time = 1.0  #Control loop interval (seconds)
# sleep_time 采样时间， kp, ki, kd，输出最小值，输出最大值，时间
#Create simple PID object with saturation value of 1023
#PID = PIDArduino(sleep_time,p,i,d,duty_min,duty_max) 
#www服务器的ip
webhost=str('10.0.0.117')
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
    s = socket.socket()
    s.connect(addr)
    #换行符是\r\n
    s.send(bytes('GET /%s HTTP/1.0\r\nHost: %s\r\n\r\n' % (path, host), 'utf8'))
    while True:
        data = s.recv(100)
        if data:
            #print(str(data, 'utf8'), end='')
            break
        else:
            break
    s.close()
#获取温度
def get_temp():   
    try:
        temp =str(rtd.temperature)
    except:
        #If sensor read fails, use a sentinel value so control loop continues but the error is obvious on the graph
        #To fail SAFE the sentinel value must be higher than the setpoint, so that the heater is gradually turned off with failed reads
        temp = 123.45
    return temp
#后续考虑变化率来提高精度
#这个是温度差与目标温度的比率
#esIndex=error/setpoint
def sousvide():
#分段进行pid
    while True:
        #当前温度，由于显示需要，默认为文本类型
        temp = get_temp()
        #当前温度和目标的差值
        error = setpoint - float(temp)
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
            #continue
        else:
        #清除
            p = 1250.442732409779707
            i = 182.200001
            d = 0.000000001
            #duty_min=32
      # 采样时间， kp, ki, kd，输出最小值，输出最大值，时间
        PID = PIDArduino(sleep_time,p,i,d,duty_min,duty_max) 
        print('{0:>10}{1:>10}{2:>10}{3:>7}{4:>10}{5:>10}{6:>10}'.format('TEMP', 'ERROR', 'DRIVE', 'DUTY', 'P', 'I', 'D'))
        temp = float(get_temp())
        error = setpoint - temp
        #if 0.0 > error and error >-0.2:
        #    error =-error*20
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
        time.sleep(sleep_time)
#进行运算
sousvide()
#timer1 = Timer(-1)  #新建一个定时器
    #每隔1秒执行一次updateTime函数调用，用于更新OLED显示屏上的时间
    #1 second=1000 milisecond,  
#timer1.init(period=1500, mode=Timer.PERIODIC, callback=sousvide())
#水具有很大的热惯性，而且PID 运算中的I（积分项）具有非常明显的延迟效应所以不能保留，我们必须把积分项去掉，相反D（微分项）则有很强的预见性，
#能够加快反应速度，抑制超调量
