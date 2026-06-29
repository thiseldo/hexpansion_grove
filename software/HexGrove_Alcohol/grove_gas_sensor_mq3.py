import math
import sys
import time
from grove.adc import ADC


class GroveGasSensorMQ3:

    def __init__(self, channel):
        self.channel = channel
        self.adc = ADC()

    @property
    def MQ3(self):
        value = self.adc.read(self.channel)
        return value

Grove = GroveGasSensorMQ3


def main():
    if len(sys.argv) < 2:
        print('Usage: {} adc_channel'.format(sys.argv[0]))
        sys.exit(1)

    sensor = GroveGasSensorMQ3(int(sys.argv[1]))

    print('Detecting...')
    while True:
        print('Gas value: {0}'.format(sensor.MQ3))
        time.sleep(.3)

if __name__ == '__main__':
    main()
