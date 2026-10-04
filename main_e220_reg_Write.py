from machine import UART, Pin, I2C
import time
from E220 import E220
import ssd1306                # 液晶表示器用ライブラリ
import _thread  # 複数のタスクを同時に実行するスレッドモジュールを準備

"""
Module Conf.
#comd = [0xc0, 0x03, 0x01, 0x00] #RSSI環境ノイズ"0"
#comd = [0xc0, 0x05, 0x01, 0x83] #RSSIバイト"1"

Register Read

"""

# UART Setting
uart0 = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))

# E220
e220 = E220(uart0, m0=2, m1=3, aux=8, rssi=True)

# pico pico-W LED pin設定
def setup_led():
    try:
        return Pin("LED", Pin.OUT)
    except:
        return Pin(25, Pin.OUT)
    
led = setup_led()

led.off()

# I2C設定 (I2C識別ID 0or1, SDA, SCL)
i2c = I2C(0, sda=Pin(16), scl=Pin(17) )

# 使用するSSD1306のアドレス取得表示（通常は0x3C）
addr = i2c.scan()
print( "OLED I2C Address :" + hex(addr[0]) )

# ディスプレイ設定（幅, 高さ, 通信仕様）
display = ssd1306.SSD1306_I2C(128, 64, i2c)

for i in range(1, 3, 1):
    #led.value(1)
    led.on()
    time.sleep(0.5)
    #led.value(0)
    led.off()
    time.sleep(0.5)

print("Stand-by ready.")

"""
# 液晶画面表示内容設定
display.fill(0) # 表示内容消去
display.text('E220 LoRa TEST', 1, 2, True)  # ('内容', x, y, 色) テキスト表示
display.show() # 設定した内容を表示
"""
def disp(t, r, c):
    #display.fill(0) # 表示内容消去
    display.fill_rect(r, c, r+127, c+7, 0)
    display.text('                ', r,c)
    display.text(t, r, c)  # ('内容', x, y, 色) テキスト表示
    display.show() # 設定した内容を表示

disp('E220 TEST3:RegR', 1, 2)
# Column 2, 12, 22, 32, 42, 52


#Register Write

# Write command: C0 + address + length + parameters

#83h -> C3h 
add = 0x05
length = 0x01
param = 0xC3

"""
#00h -> 04h
add = 0x01
length = 0x01
param = 0x04
"""

cmd = bytes([0xC0, add, length, param])

result = e220.write_config(cmd)

if result: #  == True
    print("Reg write Successful")
    disp("Reg Write", 1, 12)

    print("Address", hex(add))
    disp("Address" + hex(add), 1, 22)
    
    print("Length", hex(length))
    disp("Length" + hex(length), 1, 32)
    
    print("Param", hex(param))
    disp("Param" + hex(param), 1, 42)
else:
    print("Reg write Failed")
    disp("Write Fail", 1, 12)
    