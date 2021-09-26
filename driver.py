from machine import I2C, Pin
import time
import math

WIDTH = 128
HEIGHT = 64

class Display():
    
    def write_cmds(self, cmds): # Use the i2c interface to send commands to the display
        temp = [0x80 for i in range(len(cmds) * 2)]
        temp_cmd_index = 1
        cmds_array_index = 0
        
        while temp_cmd_index != len(temp) - 1:
            temp[temp_cmd_index] = cmds[cmds_array_index]
            
            cmds_array_index += 1
            temp_cmd_index += 2
        
        temp[-2] = 0x00
        temp[-1] = cmds[-1]
        self.i2c.writeto(self.address, bytearray(temp))

    def write_disp_data(self, data_in, page_addr, col_hi=0x10, col_lo=0x02): #Write video data to display
        data = [0x40] + data_in + [0x00, 0x00, 0x00, 0x00]
        if page_addr > 7 or page_addr < 0: # Display has 8 pages each 8 pixels tall
            print("Page address must be a positive int <= 7")
            return -1
        self.write_cmds([0xB0 + page_addr])
        
        self.write_cmds([col_lo, col_hi])
        self.i2c.writeto(self.address, bytearray(data))
        

    def on(self):
        # Sequence taken from the Waveshare SH1106 Datasheet, page 19

        self.write_cmds([0xAE]) # Display off
        self.write_cmds([0xD5, 0x80]) # Set display clk divide ratio/oscillator freq
        self.write_cmds([0xA8, 0x3F]) # Set mux ratio
        self.write_cmds([0xD3, 0x00]) # Display offset to 0
        self.write_cmds([0x40]) # Display start line to 0
        self.write_cmds([0xAD, 0x8B]) # Set charge pump
        self.write_cmds([0xA1]) # Set segment re-map
        self.write_cmds([0xC8]) # COM output scan direction
        self.write_cmds([0xDA, 0x12]) # COM pins hardware config
        self.write_cmds([0x81, 0xBF]) # Set contrast control
        self.write_cmds([0xd9, 0x22]) # Set pre-charge period
        self.write_cmds([0xDB, 0x40]) # Set VCOMH Deselect level
        self.write_cmds([0x32]) # Set VPP
        self.write_cmds([0xA6]) # Set normal (not inverse) display
        self.write_cmds([0x02, 0x10])
        self.write_cmds([0xAF]) # Set display on
        time.sleep_ms(100) # Recommended delay

    def draw(self): # Converts 2D array (frameBuffer) to a 128x8 byte array, and sends it to the display
        for y in range(HEIGHT):
            if y % 8 == 0:
                
                for x in range(WIDTH):
                    byte = 0x00
                    
                    for bit in range(8): # Push each pixel in an 8-pixel column to a byte
                        byte = byte >> 1
                        byte += 0x80 * self.frameBuffer[y + bit][x]
                    
                    self.sendBuffer[y // 8][x] = byte
                    
        page_num = 0
        for page in self.sendBuffer:
            self.write_disp_data(page, page_num)
            page_num += 1

    def draw_pixel(self, x, y, state=True): # Sets one pixel in the frameBuffer
        self.frameBuffer[y][x] = 1 * state
        
    def draw_line(self, x1, y1, x2, y2): # Draws a straight line in the frameBuffer between (x1, y1) and (x2, y2)
        xhi = max(x1, x2)
        xlo = min(x1, x2)
        yhi = max(y1, y2)
        ylo = min(y1, y2)
        
        rise = yhi - ylo
        run =  xhi - xlo
        
        if rise == 0 or run == 0:
            gradient = 0
        else:
            gradient = rise / run
        
        if not run == 0:
            for x in range(run):
                self.draw_pixel(xlo + x, round(x * gradient) + ylo)
        else:
            for y in range(rise + 1):
                self.draw_pixel(x1, y + y1)
    
    def draw_rect(self, x, y, w, h): # Draws a rectangle of width w and height h with its top left corner at (x, y)
        self.draw_line(x,   y, x+w,   y)
        self.draw_line(x,   y, x,   y+h)
        self.draw_line(x+w, y, x+w, y+h)
        self.draw_line(x, y+h, x+w, y+h)
    
    def __init__(self, addr, i2c_id=0, SCL_pin=17, SDA_pin=16, rate=400000):
        self.i2c = I2C(id=i2c_id, scl=Pin(SCL_pin), sda=Pin(SDA_pin), freq=rate) # Initialize i2c interface
        self.address = addr
        self.frameBuffer = [[0 for x in range(WIDTH)] for y in range(HEIGHT)] # Simple 128x64 pixel buffer
        self.sendBuffer = [[0 for x in range(WIDTH)] for y in range(HEIGHT // 8)] # Buffer in format acceptable by the SH1106 display