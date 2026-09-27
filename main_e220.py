from machine import UART, Pin, I2C
import time
from E220 import E220
import ssd1306                # 液晶表示器用ライブラリ
import _thread  # 複数のタスクを同時に実行するスレッドモジュールを準備

"""
Module Conf.
#comd = [0xc0, 0x03, 0x01, 0x00] #RSSI環境ノイズ"0"
#comd = [0xc0, 0x05, 0x01, 0x83] #RSSIバイト"1"

Multi thread
https://logikara.blog/pico-multicore/#toc8


"""

# UART Setting
uart0 = UART(0, baudrate=9600, tx=Pin(0), rx=Pin(1))

#uart1 = UART(1, baudrate=9600, tx=Pin(4), rx=Pin(5))

# E220
e220 = E220(uart0, m0=2, m1=3, aux=8, rssi=True)

#radio1 = E220(uart0, m0=2, m1=3, aux=8, rssi=True)

# 入力ピン設定
SW_TX = Pin(15, Pin.IN, Pin.PULL_UP)  # スイッチのピン番号を指定してswとして入力設定（プルアップ）

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

# 変数宣言（スレッドで共有する変数は配列で指定）
cnt = [0]  # スレッドで共有する変数

#rxData = bytes()
#brxData = bytes()

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

disp('E220 LoRa TEST3', 1, 2)
# Column 2, 12, 22, 32, 42, 52

while True:
    #rxData : 受け取ったデータバイト列
    #brxData : 最後のrssiバイトを除いたデータバイト列
    #srxData : brxDataを文字列へ変換したStrings
    #srxDataT : srxDataの13文字目以降
    
    #Receive data
    rxData = e220.receive()

    if rxData is not None:
        
        led.on()     # 本体LEDを点灯
        
        #print("RX:", rxData)
    
        # ここで受信データを処理する
        #if rxData.startswith(b"T001"):
    
        print("Received byte length :", len(rxData))

        # 最後の1byteをRSSIとして除外
        brxData = rxData[:-1]

        # UTF-8変換
        try:
            srxData = brxData.decode('utf-8')
        except Exception:
            srxData = None

        # HEX表示
        print(' '.join(f'{b:02X}' for b in rxData))

        # 文字列処理
        srxDataT=""
        
        if srxData is not None:

            cod = srxData.find('T001')

            if cod == 0:
                print("Key word index :", cod)
                print(srxData)
                srxDataT = srxData[14:]
                print(srxDataT)
            else:
                print("No key word")

        else:
            print("UTF-8 decode error")

        # RSSI
        rssi = int(rxData[-1]) - 256

        print(f"RSSI: {rssi} dBm")

        print(f"AUX: {e220.aux.value()}")

        disp('E220 TEST3:Resv', 1, 2)
        disp('StLn:' + str(len(rxData)) + 'byt', 1, 12)
        disp(srxData[0:4], 1, 22)
        disp('StVa: ' + srxDataT + ' deg', 1, 32)
        disp('RSSI: ' + str(rssi) + ' dBm', 1, 42)
        disp('------------------', 1, 52)
        
        led.off()     # 本体LEDを消灯
    
    
    #Send data
    if SW_TX.value() == 0:  # スイッチが押されていたら
        led.on()     # 本体LEDを点灯
        cnt[0] += 1         # カウント+1
        
        #送信データを処理
        txData = b'T001 req act :'+ str(cnt[0]).encode()
        
        e220.send(txData)
        
        led.off()     # 本体LEDを消灯
        
        # スイッチが離されるまで待つ
        while SW_TX.value() == 0:
            time.sleep_ms(10)
        
        disp('E220 TEST3:Sent', 1, 2)

    time.sleep_ms(10)

