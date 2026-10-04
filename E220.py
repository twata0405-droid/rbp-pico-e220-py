from machine import Pin
import time

"""
Ver 01.01 2026.09.26 : wait_aux H(Normal) to L(Busy) to H(Normal), Syntax調整
Ver 01.02 2026.10.01 : read_rssi_noise()追加 AUX固着症状回避策
                        read_config(self, add), write_config(self, cmd)追加
                        set_mode(self, mode)修正、wait_aux_ready追加
Ver 01.03 2026.10.04 : Fixed Send mode
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
    
    def read_rssi_noise(self):
        cmd = bytes([0xC0, 0xC1, 0xC2, 0xC3, 0x00, 0x02])
        self.uart.write(cmd)
    

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

        if mode not in (
            self.MODE_NORMAL,
            self.MODE_WOR_TX,
            self.MODE_WOR_RX,
            self.MODE_CONFIG
        ):
            raise ValueError("Invalid mode")

        # モード切替前にAUXがHIGHになるのを待つ
        if not self.wait_aux_ready():
            raise Exception("E220 AUX not ready before mode change")

        if mode == self.MODE_NORMAL:
            self.m0.value(0)
            self.m1.value(0)

        elif mode == self.MODE_WOR_TX:
            self.m0.value(1)
            self.m1.value(0)

        elif mode == self.MODE_WOR_RX:
            self.m0.value(0)
            self.m1.value(1)

        elif mode == self.MODE_CONFIG:
            self.m0.value(1)
            self.m1.value(1)

        # モード切替後の安定待ち
        time.sleep_ms(2)

        if not self.wait_aux_ready():
            raise Exception("E220 AUX timeout after mode change")

        self.mode = mode
        
    def wait_aux_ready(self, timeout_ms=2000):

        start = time.ticks_ms()

        while self.aux.value() == 0:

            if time.ticks_diff(
                time.ticks_ms(), start
            ) >= timeout_ms:
                return False

            time.sleep_ms(1)

        return True


    # --------------------------------------------------
    # Configuration : Read Register
    # --------------------------------------------------
    def read_config(self, add):

        if not 0 <= add <= 0xFF:
            raise ValueError("Invalid register address")

        old_mode = self.mode

        try:
            # Configuration mode
            self.set_mode(self.MODE_CONFIG)

            # Configuration mode UART: 9600bps, 8N1
            # このメソッドを呼ぶ前にUARTが9600bpsであること
            # （下記の注意事項を参照）
            
            """ #debug
            print("Mode =", self.mode)
            print("M0 =", self.m0.value())
            print("M1 =", self.m1.value())
            print("AUX =", self.aux.value())
            # """

            # 古い受信データをクリア
            while self.uart.any():
                self.uart.read()
                """ #debug
                print("Discard =", self.uart.read())
                # """
            
            #debug
            # AUXがHIGHになるまで待つ
            if not self.wait_aux_ready():
                raise Exception("E220 AUX not ready before read")

            # コマンド間隔を確保(50ms必要　20msではNG)
            time.sleep_ms(50)
            
            # Read command: C1 + address + length
            cmd = bytes([0xC1, add, 0x01])
            """ #debug
            print("TX command =", cmd.hex())
            # """
            self.uart.write(cmd)

            # 4 bytes: C1 + address + length + value
            response = self._read_response(4)

            # 次の設定コマンドまでの待ち時間
            #time.sleep_ms(50)

            if response[0] != 0xC1:
                raise Exception("Invalid read response command")

            if response[1] != add or response[2] != 0x01:
                raise Exception("Invalid read response header")

            return response[3]

        finally:
            self.set_mode(old_mode)


    # --------------------------------------------------
    # Configuration : Write Register
    # --------------------------------------------------
    def write_config(self, cmd):

        if isinstance(cmd, list):
            cmd = bytes(cmd)

        if not isinstance(cmd, bytes):
            raise TypeError("cmd must be bytes or list")

        if len(cmd) < 4 or cmd[0] != 0xC0:
            raise ValueError("Invalid write command")

        add = cmd[1]
        length = cmd[2]

        if length < 1 or len(cmd) != 3 + length:
            raise ValueError("Invalid write command length")

        old_mode = self.mode

        try:
            # Configuration mode
            self.set_mode(self.MODE_CONFIG)

            # 古い受信データをクリア
            while self.uart.any():
                self.uart.read()

            #debug
            # AUXがHIGHになるまで待つ
            if not self.wait_aux_ready():
                raise Exception("E220 AUX not ready before write")

            # コマンド間隔を確保(50ms必要　20msではNG)
            time.sleep_ms(50)
            

            # Write command
            self.uart.write(cmd)

            # Response: C1 + address + length + parameters
            response = self._read_response(3 + length)

            if response[0] != 0xC1:
                raise Exception("Invalid write response command")

            if response[1] != add or response[2] != length:
                raise Exception("Invalid write response header")

            if response[3:] != cmd[3:]:
                raise Exception("Write verify failed")

            return True

        finally:
            self.set_mode(old_mode)


    # --------------------------------------------------
    # Configuration : Read UART response
    # --------------------------------------------------
    def _read_response(self, length, timeout_ms=1000):

        response = bytearray()
        start = time.ticks_ms()

        while len(response) < length:

            if self.uart.any():
                data = self.uart.read(length - len(response))

                if data:
                    response.extend(data)

            if time.ticks_diff(time.ticks_ms(), start) >= timeout_ms:
                
                """ #debug
                print("Config response timeout")
                print("Expected length =", length)
                print("Received length =", len(response))
                print("Received data   =", bytes(response))
                print("Received hex    =", bytes(response).hex())
                print("AUX              =", self.aux.value())
                print("UART pending     =", self.uart.any())
                # """
                raise Exception(
                    "E220 configuration response timeout"
                )

            time.sleep_ms(1)
            
        """ #debug
        print("Expected length =", length)
        print("Received length =", len(response))
        print("Received data   =", bytes(response))
        print("Received hex    =", bytes(response).hex())
        print("Config response =", response.hex())
        # """
        return bytes(response)
        
        
    #def reset():
            
    #Instanceが有効か返す if Instance.available():            
    def available(self):
        
        return self.uart.any()
