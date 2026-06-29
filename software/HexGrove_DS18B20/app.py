import app

from machine import I2C
from system.hexpansion.config import HexpansionConfig
from app_components import clear_background, Menu
from app_components.tokens import colors
from events.input import Buttons, BUTTON_TYPES
from system.eventbus import eventbus
from system.hexpansion.events import HexpansionRemovalEvent, HexpansionInsertionEvent
from system.hexpansion.util import read_hexpansion_header, detect_eeprom_addr
#from machine import ADC
from .onewire import DS18X20
from .onewire import OneWire
import time


class HexGrove_DS18B20(app.App):
    def __init__(self):
        self.button_states = Buttons(self)
        self.text = "No hexpansion found."
        self.color = (1, 0, 0)
        self.found_hexpansion = False
        self.hexpansion_config = None
        self.pins = None
        self.ow = None
        self.temp = None
        self.value = 0.0
        self.scan_for_hexpansion()

        eventbus.on(
            HexpansionInsertionEvent,
            self.handle_hexpansion_insertion,
            self)
        eventbus.on(
            HexpansionRemovalEvent,
            self.handle_hexpansion_removal,
            self)

    def handle_hexpansion_insertion(self, event):
        self.scan_for_hexpansion()

    def handle_hexpansion_removal(self, event):
        self.found_hexpansion = False
        self.ow = None
        self.temp = None
        self.pins = None
        self.hexpansion_config = None
        self.scan_for_hexpansion()

    def update(self, delta):
        if self.button_states.get(BUTTON_TYPES["CANCEL"]):
            self.button_states.clear()
            self.minimise()
        
        if self.temp:
            # perform temperature reading
            self.temp.start_convertion()
            time.sleep(1)
            self.value = self.temp.read_temp_async()


    def draw(self, ctx):
        ctx.save()
        clear_background(ctx)
        if self.temp:
            x, y, z = self.color
            textstr = "{:.2f}C".format(self.value)
            ctx.rgb(x, y, z).move_to(-40, -30).text(textstr)
        else:
            x, y, z = self.color
            ctx.rgb(x, y, z).move_to(-90, -40).text(self.text)
        ctx.restore()

    def scan_for_hexpansion(self):
        found = False
        for port in range(1, 7):
            print(f"Searching for hexpansion on port: {port}")
            i2c = I2C(port)
            addr, addr_len = detect_eeprom_addr(i2c)

            if addr is None:
                continue
            else:
                print("Found EEPROM at addr " + hex(addr))

            header = read_hexpansion_header(i2c, addr, addr_len=addr_len)
            if header is None:
                continue
            else:
                print("Read header: " + str(header))

            self.text = "Hexp. found.\nvid: {}\npid: {}\nat port: {}".format(
                hex(header.vid), hex(header.pid), port)
            found = True

            if (header.vid == 0xF055) and (header.pid == 0x2305):
                print("Found the desired hexpansion in port " + str(port))
                self.color = (0, 1, 0)
                self.found_hexpansion = True
                self.hexpansion_config = HexpansionConfig(port)
                self.pins = {}
                self.pins["hs_1"] = self.hexpansion_config.pin[1]
                #print("Pin ")
                #print(self.pins["hs_1"])
                self.ow = OneWire(self.pins["hs_1"])
                devices = self.ow.scan()
                if len(devices) > 0:
                    print("DS18B20 devices found")
                    #print(self.ow.scan())
                    self.temp = DS18X20(self.ow)
            else:
                print()
        if not found:
            self.color = (1, 0, 0)
            self.text = "No hexpansion found."

        return None

__app_export__ = HexGrove_DS18B20