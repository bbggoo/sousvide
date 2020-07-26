"""
	Original by  https://github.com/umarsear/ESP8266-Connected-MP3-Player#
	Thank you umarsear for your great work!

	The board uses the jq8400 MP3 audio chip. It supports 8KHz to 48KHz sampling frequencies for MP3 and WAV file format
	
	Not all commands are mapped. 
	
	Command format
	
	Each command is 8 bytes
	Pos	Descrption 	Bytes	Value
	1 	Start		1		0xAA
	2	command		1		refer manual
	3	Lenght		1		len(data 1,....,data n)
	4	data		1		see below
	5	datan   	1		optional,refer manual
	6	SM			1		checksum of lower byte of (from Start to  datan )

	
	chinese remark below:
	#格式：起始码-指令类型-数据长度（n）-数据 1－数据 n－和检验(SM)
	#起始码-指令类型-数据长度（n）-数据 1－数据 n－和检验(SM)

	#起始码：AA ，固定

	#指令类型：用来区分指令类型

	#数据长度：指令中的数据的字节数,len()

	#数据 ：指令中的相关数据，当数据长度为 1 时,表示只有 CMD,没有数据位

	#和检验 ：为之前所有字节之和的低 8 位,即起始码到数据相加后取低 8 位
	#取低8位 ：& 0xff，  SM=cmd1 & .... & cmdn

	#eg:AA 02 00 AC
	#起始码：AA 
	#指令类型：单曲停止(02)
	#数据长度 ：0
	#数据：没有数据，只有命令
	#和检验(SM)：AA+02=AC
	#如果有多个bytes应该要累加
	chinese remark end
"""

        
#位运算，返回高八位，低8位
#to get HighByte,LowByte
def split(num):
    return num >> 8, num & 0xFF
#to get SM,
def get_SM(b):
	message_length=len(b)
	bit_sum=0X00
	#按位与运算
	for i in range((message_length)):
		bit_sum += b[i]
	#print("bit_sum:",bit_sum)
  	#和检验 ：为之前所有字节之和的低 8 位,即起始码到数据相加后取低 8 位
	SM_Code=(0xAA  + bit_sum ) & 0xFF
	#print("SM_Code:",SM_Code)
 #验证：07 02 00 01，bit_sum=
	return SM_Code

def command_base():
	command=bytearray()
	command.append(0xAA)##[0]
	command.append(0x00)##[1]
	command.append(0x00)##[2]
	command.append(0x00)##[3]
	return command
#下一曲
def play_next():
	command=bytearray()
	command=command_base()
	command[1]=0x06
	command[3]=0xB0
	return command
#上一曲
def play_previous():
	command=bytearray()
	command=command_base()
	command[1]=0x05
	command[3]=0xAF
	return command

#曲目id从1-65536，拆分成高低,否则应该append	
#track_id ,1-65536
def play_track(track_id):
	command=bytearray()
	command=command_base()
	command[1]=0x07
	command[2]=0x02
	HighByte, LowByte = split(track_id)
	command[3]=HighByte
	command.append(LowByte)
	#print("HighByte:",HighByte)
	#print("LowByte:",LowByte)
	b=[command[1],command[2],command[3],command[4]]
	SM_Code=get_SM(b) 
	command.append(SM_Code)
	return command
	
def volume_up():
	command=bytearray()
	command=command_base()
	command[1]=0x14
	command[3]=0xBE
	return command

def volume_down():
	command=bytearray()
	command=command_base()
	command[1]=0x15
	command[3]=0xBF
	return command

def set_volume(level):
	command=bytearray()
	command=command_base()
	command[1]=0x13
	command[2]=0x01
	command[3]=level
	b=[command[1],command[2],command[3]]
	SM_Code=get_SM(b) 
	command.append(SM_Code)
	return command
	
def pause():
	command=bytearray()
	command=command_base()
	command[1]=0x03
	command[3]=0xAD
	return command	
		
def stop():
	command=bytearray()
	command=command_base()
	command[1]=0x04
	command[3]=0xAE
	return command

#切换为flash卡
#AA 0B 01 02 B8 切换到 FLASH 卡，切换后处于停止状态
#use flash to play ,it's by default
def use_flash():
	command=bytearray()
	command=command_base()
	command[1]=0x0B
	command[2]=0x01
	command[3]=0x02
	command.append(0xB8) 
	return command
#指令：AA 16 03 盘符 曲目高 曲目低 SM
#返回：无
#盘符定义: 切换盘符后处于停止状态
#USB:00 SD:01 FLASH:02 NO_DEVICE：FF
#例如：AA 16 03 00 00 09 CC 插播 U 盘里的第 9 首
#说明：插播结束后返回插播点继续播放
def insert_play(track_id):
	command=bytearray()
	command=command_base()
	command[1]=0x16
	command[2]=0x03
	command[3]=0x02
	HighByte, LowByte = split(track_id)
	command.append(HighByte)
	command.append(LowByte)
	b=[command[1],command[2],command[3],command[4],command[5]]
	SM_Code=get_SM(b)
	command.append(SM_Code)
	return command