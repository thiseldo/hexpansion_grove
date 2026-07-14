"""
License
The MIT License (MIT)

Copyright (C) 2020 Ville Laine, Aikuiskoulutus Taitaja

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

from machine import I2C
from time import sleep

class SGP30:

    def __init__(self, i2c=None):
        self.bus = i2c if i2c else I2C()

        # SGP30 i2c default address is 0x58
        self.address = 0x58
        self.crc_status = [0, 0]
        self.CO2eq = 0
        self.TVOC = 0
        self.CO2eq_raw = 0
        self.TVOC_raw = 0
        self.CO2eq_baseline = 0
        self.TVOC_baseline = 0

    #########################################
    # Command functions                     #
    #########################################

    # Init air quality command
    # A new “Init_air_quality” command has to be sent after every power-up or soft reset.
    def init_air_quality(self):
        command = ([0x20, 0x03], 0, 10)
        try:
            self.read_write(command)
        except Exception:
            # On fail return 0
            print("sgp30 Init Fail!")
            return 0
        else:
            print("sgp30 Init Ok!")
            # Command pass return 1
            return 1

    # Measure compensated Co2eq and TVOC values
    # Has to be sent regular intervals 1s to ensure proper operation of dynamic baseline correction algorithm
    def measure_air_quality(self):
        command = ([0x20, 0x08], 6, 12)
        data = self.read_write(command)

        if self.crc_status[0] == 0:
            print("Measurement CRC check failed", self.crc_status)
            self.CO2eq = 0
            self.TVOC = 0
            return [0, 0]
        else:
            self.CO2eq = self.bytes_to_int(data[0:2])
            self.TVOC = self.bytes_to_int(data[3:5])
            return [self.CO2eq, self.TVOC]

    # Get compensation baseline values
    #
    def get_baseline(self):
        command = ([0x20, 0x15], 6, 10)
        try:
            data = self.read_write(command)
        except Exception:
            # On fail return 0
            print("get_baseline() => read_write() failed.")
            return 0

        if self.crc_status[0] == 0:
            print("Basevalue read CRC check failed", self.crc_status)
            return 0
        else:
            self.CO2eq_baseline = self.bytes_to_int(data[0:2])
            self.TVOC_baseline = self.bytes_to_int(data[3:5])
            return 1

    # Set compensation baseline values
    # Sets also variables sgp30(Instance).CO2eq_baseline and sgp30(Instance).TVOC_baseline
    def set_baseline(self, message):
        command = ([0x20, 0x1e], 0, 10)
        formatted_data = []

        # generate correct message format [HByte, LByte, CRC, HByte, LByte, CRC, ...]
        for number in message:
            tmp_bytes = self.int_to_bytes(number)
            crc = self.calc_crc8(tmp_bytes)
            formatted_data.extend(tmp_bytes)
            formatted_data.append(crc)

        # Extend command data with with message
        command[0].extend(formatted_data)

        try:
            self.read_write(command)
        except Exception:
            # On fail return 0
            print("set_baseline() => read_write() failed.")
            return 0
        else:
            self.TVOC_baseline = message[0]
            self.CO2eq_baseline = message[1]
            print("Compensation baseline values writen successfully.")
            return 1

    # Set humidity compensation value
    #
    def set_humidity(self, message):
        command = ([0x20, 0x61], 0, 10)
        formatted_data = []

        # generate correct message format [HByte, LByte, CRC, HByte, LByte, CRC, ...]
        for number in message:
            tmp_bytes = self.int_to_bytes(number)
            crc = self.calc_crc8(tmp_bytes)
            formatted_data.extend(tmp_bytes)
            formatted_data.append(crc)

        # Extend command data with with message
        command[0].extend(formatted_data)

        try:
            self.read_write(command)
        except Exception:
            # On fail return 0
            print("set_humidity() => read_write() failed.")
            return 0
        else:
            print("Humidity compensation value writen successfully.")
            return 1

    # Measure test
    # The command “Measure_test” which is included for integration and production line testing runs an on-chip
    # self-test. In case of a successful self-test the sensor returns the fixed data pattern 0xD400 (with correct CRC)
    def measure_test(self):
        command = ([0x20, 0x32], 3, 220)
        data = self.read_write(command)

        if self.crc_status[0] == 0:
            print("Measurement CRC check failed", self.crc_status)
            return 0
        else:
            print("On-chip self-test succesfull!")
            return self.bytes_to_int(data[0:2])

    def get_feature_set_version(self):
        command = ([0x20, 0x2f], 3, 2)
        data = self.read_write(command)

        print("Product type: ", '{0:08b}'.format(data[0])[0:4])
        print("Product version: ", '{0:08b}'.format(data[1]) + ", " + str(data[1]))

    def measure_raw_signals(self):
        command = ([0x20, 0x50], 6, 25)
        data = self.read_write(command)

        if self.crc_status[0] == 0:
            print("Measurement CRC check failed", self.crc_status)
            self.CO2eq_raw = 0
            self.TVOC_raw = 0
            return 0
        else:
            self.CO2eq_raw = self.bytes_to_int(data[0:2])
            self.TVOC_raw = self.bytes_to_int(data[3:5])
            return 1

    # Soft reset command
    # A sensor reset can be generated using the “General Call” mode according to I2C-bus specification.
    # It is important to understand that a reset generated in this way is not device specific.
    # All devices on the same I2C bus that support the General Call mode will perform a reset.
    def soft_reset(self):
        command = ([0x00, 0x06], 0, 10)
        self.read_write(command)

    # Get serial ID
    def get_serial_id(self):
        command = ([0x36, 0x82], 9, 10)
        data = self.read_write(command)

        if self.crc_status[0] == 0:
            print("Measurement CRC check failed", self.crc_status)
            return 0
        else:
            print("Get serial succesfull!")
            print("Serial part 1: ", '{0:016b}'.format(self.bytes_to_int(data[0:2])))
            print("Serial part 2: ", '{0:016b}'.format(self.bytes_to_int(data[3:5])))
            print("Serial part 3: ", '{0:016b}'.format(self.bytes_to_int(data[7:9])))
            return 1

    #########################################
    # read and write data to the sgp30      #
    #########################################
    def read_write(self, command):
        if command[1] <= 0:
            # Write to I2C-bus
            # write_i2c_block_data(address, offset, [data_bytes])
            # Note that second offset byte is [data_bytes][0]
            #self.bus.write_i2c_block_data(self.address, command[0][0], command[0][1:])
            self.bus.writeto(self.address, bytes([command[0][0]]) + bytes(command[0][1:]))
            sleep(command[2]/1000)
            return 1
        else:
            # Read (Write and read) from I2C-Bus
            # write_i2c_block_data(address, offset, [data_bytes])
            # Note that second offset byte is [data_bytes][0]
            # read_i2c_block_data(address, offset, number_of_data_bytes)
            #self.bus.write_i2c_block_data(self.address, command[0][0], [command[0][1]])
            self.bus.writeto(self.address, bytes([command[0][0]]) + bytes([command[0][1]]))
            sleep(command[2]/1000)
            #data = self.bus.read_i2c_block_data(self.address, 0, command[1])
            data = self.bus.readfrom(self.address, command[1])
            self.crc_status = self.validate_crc8(data)
            return data

    # Necessary functions
    def calc_crc8(bytes_list):
        # CRC init value
        crc = 0xff

        # loop through bytes
        for i in bytes_list:
            for bit in range(0, 8):
                if (i ^ crc) & 0x80:
                    crc = (crc << 1) ^ 0x31
                else:
                    crc = (crc << 1)
                i = i << 1
            crc = crc & 0xFF

        return crc


    # Convert two bytes to one int(word) = int(HByte+LByte)
    # example (HByte = 0x0a, LByte = 0xf4) = 0x0af4 = 2804
    # Returns hexadecimal representation
    def bytes_to_int(self,bytes_list):
        return_str = ""

        for i in bytes_list:
            temp_str = str(hex(i))[2:]

            # Add trailing zero if value is 0x0
            if int(temp_str, 16) == 0:
                temp_str = temp_str + "0"
            return_str = return_str + temp_str

        return int(return_str, 16)


    # Convert int(word) = int(HByte+LByte) into two bytes
    # example 2804 = 0x0af4 = (HByte = 0x0a, LByte = 0xf4)
    def int_to_bytes(self,number):
        tmp_str = str(hex(number))
        hbyte = "0x"+tmp_str[2:4]
        lbyte = "0x"+tmp_str[-2:]
        return [int(hbyte, 16), int(lbyte, 16)]

    def validate_crc8(self,int_list):
        ok = 1
        pos = 0
        values = []
        size = 3

        # Split list
        while len(int_list) > size:
            pice = int_list[:size]
            values.append(pice)
            int_list = int_list[size:]
            values.append(int_list)

        # loop through all words and respective crc [HByte, LByte, CRC]
        for value in values:
            pos = pos + 1

            # CRC init value
            crc = 0xff

            # loop through only HByte and LByte
            for i in value[0:2]:
                for bit in range(0, 8):
                    if (i ^ crc) & 0x80:
                        crc = (crc << 1) ^ 0x31
                    else:
                        crc = (crc << 1)
                    i = i << 1
                crc = crc & 0xFF

            # Check CRC status when word processed and exit if crc checksum fails
            if crc != value[2]:
                ok = 0
                # crc_status = [ok, pos]
                print("crc check failed!")
                return [ok, pos]

        if ok == 1:
            pos = 0
        # crc_status = [ok, pos]
        return [ok, pos]

