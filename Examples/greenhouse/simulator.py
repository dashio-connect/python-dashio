"""A simulated greenhouse for the greenhouse controller example.

Replace this module to control a real greenhouse: read() would read a temperature and humidity sensor
(e.g. a BME280 or DHT22) and set_outputs() would switch relays for the heater, fan and lights (e.g. with
gpiozero on a Raspberry Pi). The controller only uses read() and set_outputs().
"""
import math
import random
import time


class GreenhouseSimulator:
    """A greenhouse whose temperature and humidity respond to the weather outside and to its outputs."""

    def __init__(self):
        self.temperature = 16.0
        self.humidity = 70.0
        self._heater = False
        self._fan = False
        self._lights = False
        self._last_read = time.time()

    @staticmethod
    def outside_temperature() -> float:
        """A day/night cycle between about 6C at 3am and 20C at 3pm."""
        now = time.localtime()
        hours = now.tm_hour + now.tm_min / 60.0
        return 13.0 + 7.0 * math.sin((hours - 9.0) / 24.0 * 2.0 * math.pi)

    def set_outputs(self, heater: bool, fan: bool, lights: bool):
        """Switch the heater, fan and lights."""
        self._heater = heater
        self._fan = fan
        self._lights = lights

    def read(self) -> tuple[float, float]:
        """Returns the temperature in C and the relative humidity in %."""
        now = time.time()
        seconds = min(now - self._last_read, 60.0)
        self._last_read = now

        # The greenhouse drifts towards the outside temperature, faster with the fan on.
        leak = 0.0015 + (0.004 if self._fan else 0.0)
        self.temperature += (self.outside_temperature() - self.temperature) * leak * seconds
        if self._heater:
            self.temperature += 0.012 * seconds
        if self._lights:
            self.temperature += 0.002 * seconds

        # Plants keep the air humid. Heating and venting dry it.
        self.humidity += (80.0 - self.humidity) * 0.002 * seconds
        if self._heater:
            self.humidity -= 0.02 * seconds
        if self._fan:
            self.humidity -= 0.05 * seconds
        self.humidity = min(max(self.humidity, 20.0), 100.0)

        temperature = self.temperature + random.uniform(-0.1, 0.1)
        humidity = self.humidity + random.uniform(-0.5, 0.5)
        return round(temperature, 1), round(humidity, 1)
