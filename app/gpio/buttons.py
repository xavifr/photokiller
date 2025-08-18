from __future__ import annotations

try:
    import RPi.GPIO as GPIO  # type: ignore
except Exception:  # pragma: no cover - not available off Pi
    GPIO = None  # type: ignore

from typing import Callable


class GpioButtons:
    def __init__(self, shoot_pin: int, print_pin: int, on_shoot: Callable[[], None], on_print: Callable[[], None]):
        if GPIO is None:
            raise RuntimeError("RPi.GPIO not available")
        self.shoot_pin = shoot_pin
        self.print_pin = print_pin
        self.on_shoot = on_shoot
        self.on_print = on_print

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.shoot_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.print_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        GPIO.add_event_detect(self.shoot_pin, GPIO.FALLING, callback=lambda ch: self.on_shoot(), bouncetime=300)
        GPIO.add_event_detect(self.print_pin, GPIO.FALLING, callback=lambda ch: self.on_print(), bouncetime=300)

    def cleanup(self) -> None:
        if GPIO is not None:
            GPIO.cleanup()


