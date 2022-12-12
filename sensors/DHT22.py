'''
******************************************************************************
  * @file    Temperature Humidity Sensor - PIO.py
  * @author  Waveshare Team
  * @version 
  * @date    2021-02-08
  * @brief   Temperature Humidity Sensor.
  ******************************************************************************
  * @attention
  *
  * THE PRESENT FIRMWARE WHICH IS FOR GUIDANCE ONLY AIMS AT PROVIDING CUSTOMERS
  * WITH CODING INFORMATION REGARDING THEIR PRODUCTS IN ORDER FOR THEM TO SAVE
  * TIME. AS A RESULT, WAVESHARE SHALL NOT BE HELD LIABLE FOR ANY
  * DIRECT, INDIRECT OR CONSEQUENTIAL DAMAGES WITH RESPECT TO ANY CLAIMS ARISING
  * FROM THE CONTENT OF SUCH FIRMWARE AND/OR THE USE MADE BY CUSTOMERS OF THE
  * CODING INFORMATION CONTAINED HEREIN IN CONNECTION WITH THEIR PRODUCTS.
  *
  ******************************************************************************
'''

import utime
from rp2 import PIO, asm_pio
from machine import Pin

'''
DHT22 single-bus protocol
First, your MCU pulls the bus down by about 20ms
The MCU then releases the bus, and the bus is pulled up in 1,2uS due to the pull-up resistor
DHT22 has a response time, which is usually between 2 and 40μs
DHT22 responds by first pulling the bus down about 80μs and then pulling it up about 80μs
When the response time of DHT22 is completed, the data will be sent. First, pull the bus down about 50μs and then pull the bus up
If the high level duration of the bus is 20~30us, then the data sent is 0
If the high level duration of the bus is about 70μs, the data sent this time is 1
'''




@asm_pio(set_init=(PIO.OUT_HIGH),autopush=True, push_thresh=8)
def DHT22_PIO():
    
    # Send the start signal
    mov(y,1)               
    pull()                  
    mov(x,osr)                
    set(pindirs,1)             
    set(pins,0)                
    label ('start')
    jmp(x_dec,'start')         
    set(pindirs,0)
    
    # The bus should turn high for a short time after releasing the bus
    set(x,31)
    label("phase_A")
    jmp(pins,"goto_B")
    jmp(x_dec , "phase_A")
    
    # Error in transmission, fast output 40 bits of data to end the transmission
    label("Error")
    in_(y,1)
    jmp("Error")          
    
    
    # The slave will have a reaction time of about 40μs after releasing the bus
    label("goto_B")
    set(x,31)
    label("phase_B")
    jmp(x_dec , "Stage_B")
    jmp('Error')
    label("Stage_B")
    jmp(pin,"phase_B")
    
    
    # Starting from the machine to respond, pull the bus low 80us
    set(x,31)                  
    label('phase_C')
    jmp(pin,'goto_D')              
    jmp(x_dec,'phase_C')         
    jmp('Error')
    
    # The slave response pulls up the bus 80us
    label('goto_D')
    set(x,31)                
    label('phase_D')
    jmp(x_dec,'Stage_D')        
    jmp('Error')              
    label('Stage_D')
    jmp(pin,'phase_D')        
    
    
    # return data from the machine, first return 50us low level represents the start of return data
    set(x,31)
    label('phase_E')
    jmp(pin,'goto_F')           
    jmp(x_dec,'phase_E')         
    jmp('Error')              
    
    
    # Return data from the machine, determine whether it is 0 or 1 by the time to return high level, if 0, the duration of high level is less than 40us
    label('goto_F')              
    nop() [20]                 
    in_(pins,1)                
    set(x,31)                  
    jmp('phase_D')              
    
    
    
class DHT22:
    
    def __init__(self,Pin,smID = 0):
        self.Pin = Pin
        self.smID = smID
        self.Pin.init(Pin.IN, Pin.PULL_UP)
        # Create a state machine with the serial number self.smID
        self.sm= rp2.StateMachine(self.smID) 
    
    def read(self):
        utime.sleep_ms(100)
        #start state machine
        self.sm.init(DHT22_PIO,freq=500000,set_base=self.Pin,in_base = self.Pin ,out_base = self.Pin ,jmp_pin = self.Pin)
        # pass in delay data
        self.sm.put(10000)
        self.sm.active(1) 
        value = []
        # Retrieve data from a state machine
        for i in range(5):
            value.append(self.sm.get())
        self.sm.active(0)
        
        varify = 0
        for i in range(4):
            varify += value[i]
        if(varify & 0xff) == value[4]:
            humidity = ((value[0]<<8) + value[1])/10 
            temperature =( (value[2]<<8) + value[3])/10 
            return temperature, humidity
        else:
            return None, None

if __name__ == "__main__":
    from time import sleep
    from machine import Pin
    
    DHT22_Transport = DHT22(Pin(28))
    while True:
        temperature,humidity = DHT22_Transport.read()
        if temperature is None:
            print("Data Error")
        else:
            print("{:3.1f}'C {:3.1f}%".format(temperature,humidity))
        # If the delay time is too short, DHT22 may not respond. It is recommended to delay more than 1s
        sleep(1.5)

