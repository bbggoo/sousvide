# MicroPython Imports
import time
import machine
# import network
# import gc
# import ujson as json
# from _thread import start_new_thread
# Local Imports
#from adafruit_max31865 import MAX31865
import adafruit_max31865 as max31865

#import adafruit_max31865 as max31865
RTD_NOMINAL = 100.0  # Resistance of RTD at 0C
RTD_REFERENCE = 430.0  # Value of reference resistor on PCB
RTD_WIRES = 3          ## RTD 3 wires
# Create Software SPI controller.
# MAX31865 requires polarity of 0 and phase of 1.
# Currently, the micropython on the ESP32 does not support hardware SPI
#max31865         GPIO引脚       功能
#cs1              5             片选
#sck              18             时钟
#mosi             23             数据
#miso             19             主设备数据输入
#Vcc              电压3.3V           电源
#Gnd              地               地
sck = machine.Pin(18, machine.Pin.OUT)
mosi = machine.Pin(23, machine.Pin.IN)
miso = machine.Pin(19, machine.Pin.OUT)
# Create SPI Chip Select pins
cs1 = machine.Pin(5, machine.Pin.OUT, value=1)

spi = machine.SPI(baudrate=115200, sck=sck, mosi=mosi,
                  miso=miso, polarity=0, phase=1)

#sensor = max31865.MAX31865(spi, cs1, rtd_nominal=100, ref_resistor=430.0, wires=3)
rtd = max31865.MAX31865(spi, cs=cs1, wires=RTD_WIRES,
                        rtd_nominal = RTD_NOMINAL, ref_resistor = RTD_REFERENCE)
'''
css = [cs1]
idx         = 0
sensors     = []

for cs in css:
    idx += 1

    sensors.append(
            max31865.MAX31865(
                spi, css[idx-1],
                wires        = RTD_WIRES,
                rtd_nominal  = RTD_NOMINAL,
                ref_resistor = RTD_REFERENCE)
    )

def timestamp():
    return float(time.ticks_ms()) / 1000.0
    
boot_time = timestamp()

while True:
    #data = [timestamp() - boot_time] + [sensor.temperature ]
    data = [timestamp() - boot_time] + [sensor.temperature for sensor in sensors]
    print(','.join(map(str,data)))
    '''