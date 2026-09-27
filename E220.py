from machine import Pin
import time

"""
Ver 01.01 2026.09.26 : wait_aux H(Normal) to L(Busy) to H(Normal), Syntax調整
                        
"""


class E220:

    MODE_NORMAL = 0
    MODE_WOR_TX = 1
    MODE_WOR_RX = 2
    MODE_CONFIG = 3
    SEND_MODES = (MODE_NORMAL, MODE_WOR_TX)
    RECEIVE_MODES = (MODE_NORMAL, MODE_WOR_RX)

    def __init__(self, uart, m0, m1, aux, rssi=True):

        self.uart = uart

        self.m0 = Pin(m0, Pin.OUT)
        self.m1 = Pin(m1, Pin.OUT)
        self.aux = Pin(aux, Pin.IN, Pin.PULL_UP)
        self.rssi = rssi
        
        # set mode-0 (default normal mode)
        self.set_mode(self.MODE_NORMAL)

    # print(repr(ObjectName)), print(ObjectName) (__str__未定義の場合)
    def __repr__(self):
        return f"E220(mode={self.mode})"
    
   
    def send(self, data, mode = None):
        
        if mode is not None: #modeの指定がある場合
            if mode not in self.SEND_MODES: #mode指定がSEND以外の場合
                raise Exception("Invalid send mode")
        
            if mode != self.mode: #(modeの指定がある場合)、mode指定がSENDに合致
                self.set_mode(mode)
            
        if isinstance(data, str):
            data = data.encode("utf-8")
        
        self.uart.write(data)
        
        self.wait_aux()
        
        
    #UARTに現在存在するデータを読み取り
    def receive(self, mode=None):
    
        if mode is not None: #modeの指定がある場合
            if mode not in self.RECEIVE_MODES: #mode指定がRECEIVE以外の場合
                raise Exception("Invalid receive mode")
        
            if mode != self.mode: #(modeの指定がある場合)、mode指定がRECEIVEに合致
                self.set_mode(mode)

        if self.uart.any() == 0:
            return None

        return self.uart.read()
        

    def wait_aux(self, timeout_ms=2000):
        start = time.ticks_ms()
        
        # AUXがLOWになるのを待つ
        while self.aux.value() == 1:
            if time.ticks_diff(time.ticks_ms(), start) > timeout_ms:
                raise Exception("E220 AUX LOW timeout")
            time.sleep_ms(1)
        
        # AUXがHIGHになるのを待つ
        while self.aux.value() == 0:
            if time.ticks_diff(time.ticks_ms(), start) > timeout_ms:
                raise Exception("E220 AUX HIGH timeout")
            time.sleep_ms(1)

 
    def set_mode(self, mode):
        #match mode:
            #case 0:    #Normal mode
            if mode == self.MODE_NORMAL:
                self.m0.value(0)
                self.m1.value(0)
                
            #case 1:    #WOR send mode
            elif mode == self.MODE_WOR_TX:
                self.m0.value(1)
                self.m1.value(0)
                
            #case 2:    #WOR receive mode
            elif mode == self.MODE_WOR_RX:
                self.m0.value(0)
                self.m1.value(1)
                
            #case 3:    #Config mode
            elif mode == self.MODE_CONFIG:
                self.m0.value(1)
                self.m1.value(1)
                
            self.mode = mode
            
            # モード切替後、AUXがHIGHになるのを待つ
            while self.aux.value() == 0:
                time.sleep_ms(10)
            # モード切替時に「AUXがLOWになる→HIGHになる」を必ず要求しない
        
    #def read_config():
        
        
    #def write_config():
        
        
    #def reset():
            
    #Instanceが有効か返す if Instance.available():            
    def available(self):
        
        return self.uart.any()
