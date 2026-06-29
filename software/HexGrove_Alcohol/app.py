import app

from machine import I2C
from system.hexpansion.config import HexpansionConfig
from app_components import clear_background, Menu
from app_components.tokens import colors
from events.input import Buttons, BUTTON_TYPES
from system.eventbus import eventbus
from tildagonos import tildagonos
from system.hexpansion.events import HexpansionRemovalEvent, HexpansionInsertionEvent
from system.hexpansion.util import read_hexpansion_header, detect_eeprom_addr
from system.patterndisplay.events import PatternDisable, PatternEnable, PatternReload
from machine import ADC
import time

class GroveGasSensorMQ3:

    def __init__(self, pin):
        self.channel = pin
        self.adc = ADC(pin)

    @property
    def MQ3(self):
        value = self.adc.read()     #self.channel)
        return value


class HexGrove_Alcohol(app.App):
    def __init__(self):
        self.button_states = Buttons(self)
        self.text = "No hexpansion found."
        self.color = (1, 0, 0)
        self.found_hexpansion = False
        self.hexpansion_config = None
        self.pins = None
        self.mq3 = None
        self.value = 0.0

        # This disables the patterndisplay system module, which does the
        # default colour spinny thing
        eventbus.emit(PatternDisable())

        self.set_leds( (0,0,0) )
        self.scan_for_hexpansion()

        eventbus.on(
            HexpansionInsertionEvent,
            self.handle_hexpansion_insertion,
            self)
        eventbus.on(
            HexpansionRemovalEvent,
            self.handle_hexpansion_removal,
            self)

    def set_leds(self, colour):
        for i in range(0, 12):
            tildagonos.leds[i+1] = colour
        tildagonos.leds.write()


    def handle_hexpansion_insertion(self, event):
        self.scan_for_hexpansion()

    def handle_hexpansion_removal(self, event):
        self.found_hexpansion = False
        self.mq3 = None
        self.pins = None
        self.hexpansion_config = None
        self.scan_for_hexpansion()

    def update(self, delta):
        if self.button_states.get(BUTTON_TYPES["CANCEL"]):
            eventbus.emit(PatternEnable())
            eventbus.emit(PatternReload())
            self.button_states.clear()
            self.minimise()
        
        if self.mq3:
            # perform reading
            self.value = self.mq3.MQ3
            #self.temp.start_convertion()
            time.sleep(1)
            #self.value = self.temp.read_temp_async()


    def draw(self, ctx):
        ctx.save()
        clear_background(ctx)
        if self.value:
            if self.value > 1000:
                self.set_leds( (1,0,0) )
                self.color = (1, 0, 0)
            else:
                self.set_leds( (0,1,0) )
                self.color = (0, 1, 0)

            x, y, z = self.color
            textstr = "{:d}".format(self.value)
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
                if port > 3:
                    print("Found the desired hexpansion in port " + str(port))
                    self.color = (0, 1, 0)
                    self.found_hexpansion = True
                    self.hexpansion_config = HexpansionConfig(port)
                    self.pins = {}
                    self.pins["hs_1"] = self.hexpansion_config.pin[0]

                    self.mq3 = GroveGasSensorMQ3(self.pins["hs_1"])

                else:
                    self.color = (1, 0, 0)
                    self.text = "Please use\nport 4,5,6."

            else:
                print()
        if not found:
            self.color = (1, 0, 0)
            self.text = "No hexpansion found."

        return None

__app_export__ = HexGrove_Alcohol
