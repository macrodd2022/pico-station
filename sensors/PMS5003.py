from machine import Pin, UART
import time

class PMS5003:
    def __init__(self, tx, rx, interface=0):
        self.port = UART(interface, baudrate=9600, tx=tx, rx=rx)

    def read(self):
        rv = b''
        while True:
            ch1 = self.port.read(2)
            if ch1 == b'BM':
                rv = self.port.read(30)
                break
            time.sleep(0.1) # 防止读取太快出现问题
            
        check_sum = ord(b'B') + ord(b'M')
        for i in range(0, 28):
            check_sum = check_sum + int(rv[i])
        assert rv[28] * 256 + rv[29] == check_sum
            
        res = {'apm10': rv[2]* 256 + rv[3],
                'apm25': rv[4] * 256 + rv[5],
                'apm100': rv[6] * 256 + rv[7],
                'pm10': rv [8] * 256 + rv [9],
                'pm25': rv[10] * 256 + rv[11],
                'pm100': rv[12] * 256 + rv [13],
                'gt03um': rv[14] * 256 + rv [15],
                'gt05um': rv [16] * 256 + rv[17],
                'gt10um': rv[18] * 256 + rv[19],
                'gt25um': rv[20] * 256 + rv[21],
                'gt50um': rv [22] * 256 + rv[23],
                'gt100um': rv[24] * 256 + rv[25],
                'version': rv[26],
                'error-code': rv[27]
                }
        # print('===============\n'
        #       'PM1.0(CF=1): {}\n'
        #       'PM2.5(CF=1): {}\n'
        #       'PM10 (CF=1): {}\n'
        #       'PM1.0 (STD): {}\n'
        #       'PM2.5 (STD): {}\n'
        #       'PM10  (STD): {}\n'
        #       '>0.3um     : {}\n'
        #       '>0.5um     : {}\n'
        #       '>1.0um     : {}\n'
        #       '>2.5um     : {}\n'
        #       '>5.0um     : {}\n'
        #       '>10um      : {}'.format(res['apm10'], res['apm25'], res['apm100'],
        #                                res['pm10'], res['apm25'], res['pm100'],
        #                                res['gt03um'], res['gt05um'], res['gt10um'],
        #                                res['gt25um'], res['gt50um'], res['gt100um']))
        return res

class IAQI:
    LEVEL_INDEX = [0, 50, 100, 150, 200, 300, 400, 500]
    LEVEL_C = None

    def __init__(self, c):
        self.c = c

    @property
    def value(self):
        assert not self.LEVEL_C == None
        c_min = self.LEVEL_C[0]
        for i in range(len(self.LEVEL_C)):
            if self.c <= self.LEVEL_C[i]:
                c_min = self.LEVEL_C[i-1]
                c_max = self.LEVEL_C[i]
                break

        i_min = self.LEVEL_INDEX[i-1]
        i_max = self.LEVEL_INDEX[i]
        
        index = (i_max - i_min)/(c_max - c_min)*(self.c - c_min) + c_min
        return int(index)
    
class PM25(IAQI):
    LEVEL_C = [0, 35, 75, 115, 150, 250, 350, 500]

class PM10(IAQI):
    LEVEL_C = [0, 50, 150, 250, 350, 420, 500, 600]

if __name__ == "__main__":
    from machine import Pin
    import time
    
    reset = Pin(3, Pin.OUT, value=1)
    inst = PMS5003(tx=Pin(4), rx=Pin(5), interface=1)
    print("Item\tug/m3\tIAQI")
    
    while True:
        res = inst.read()
        print("PM2.5\t{}\t{}".format(res['pm25'], PM25(res['pm25']).value))
        print("PM10\t{}\t{}".format(res['pm10'], PM10(res['pm10']).value))
        
        time.sleep(2)

