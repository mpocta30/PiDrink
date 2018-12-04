import RPi.GPIO as GPIO
from time import sleep

GPIO.setmode(GPIO.BOARD)
GPIO.setup(5, GPIO.OUT, initial=GPIO.HIGH)
GPIO.setup(6, GPIO.OUT, initial=GPIO.HIGH)
GPIO.setup(13, GPIO.OUT, initial=GPIO.HIGH)
GPIO.setup(19, GPIO.OUT, initial=GPIO.HIGH)
GPIO.setup(26, GPIO.OUT, initial=GPIO.HIGH)
GPIO.setup(16, GPIO.OUT, initial=GPIO.HIGH)

pins = [5, 6, 13, 19, 26, 16]

for count in range(0, 5):
  for i in range(0, 5):
    GPIO.output(pins[i], GPIO.LOW) # energize relays until all on
    sleep(1)

  for i in range(0, 5):
    GPIO.output(pins[i], GPIO.HIGH) # de-energize relays until all off
    sleep(1)

GPIO.cleanup()
