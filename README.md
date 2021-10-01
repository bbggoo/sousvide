I have code a sousvide by micrpython ,it has incredible precision.

To get whole thing work, you will need:

1.HARDWARE:

1.1 waterproof PT-100 sensor * 1

1.2 Max31865 module * 1

1.3 128*64 oled display with spi interface, and with sh1106 controller * 1

1.4 ESP32 board * 1

1.5 EC11 Rotary Encoder * 1

1.6 button switches * 4

1.7 Solid State Relay,3-30V DC Input , control 220V AC * 1

1.8 JQ8400 mp3 decoder * 1 (optional)


2.SOFTWARE:

micropython 1.12 and above

uasyncio v3, by peterhinch

https://github.com/peterhinch/micropython-async/tree/master/v3


3.COPYRIGHT
All of this code is free for personal use, commercial use is not free.

Most of The code origin by author list below,Thank for their great job!

3.1 Max31865

origin by  https://learn.adafruit.com/adafruit-max31865-rtd-pt100-amplifier/python-circuitpython

3.2 web interface

origin by https://hackaday.io/project/153281-super-accurate-sousvide-on-a-budget,

and I add conn.php as a connnection string,every php file read connnection string,you don't need modified each file.

add mysql.sql ,also fix some bug. 

Just dowload zip file,unzip to your web server root directory. In linux ,you may need chmod a+x for php files.

Run mysql.sql in phpmyadmin will create a database.Edit conn.php to fit your envirment.

Test passed with php 7.3 , Apache 2.4.29 ,mysql 8.04 ,windows 7 professional x64.

3.3 pid liberary

origin by https://github.com/hirschmann/pid-autotune ,it is the best pid liberary i haver ever seen

3.4 uasyncio v3

https://github.com/peterhinch/micropython-async/tree/master/v3, by peterhinch, button switches also included

3.5 finite state machine

modified from code below,by StoryMonster

https://blog.csdn.net/StoryMonster/article/details/99443480?utm_medium=distribute.pc_relevant.none-task-blog-baidujs-1

3.6 sh1106 oled driver

https://github.com/raspberrypi/pico-micropython-examples/tree/master/i2c/1106oled

3.7 chinese display

http://wk20.cn/?t=118

3.8 ntp time liberary

https://github.com/micropython/micropython/blob/master/ports/esp8266/modules/ntptime.py

3.9 Rotary Encoder

https://github.com/SpotlightKid/micropython-stm-lib/blob/master/encoder/encoder.py

Hope you enjoy the code

History：
version 0.2 in progress
chinese display utility GT20L16S1Y chinese font chip ,https://www.cnblogs.com/katachi/p/9629565.html abandened,just use http://wk20.cn/?t=118
 
Using more simple sh1106 oled driver, https://www.cnblogs.com/katachi/p/9629565.html replace by https://github.com/raspberrypi/pico-micropython-examples/tree/master/i2c/1106oled

Rotary Encoder(https://github.com/MikeTeachman/micropython-rotary) not comptible with uasync, https://github.com/SpotlightKid/micropython-stm-lib/blob/master/encoder/encoder.py  instead

version 0.1  on 27 Jul 2020



