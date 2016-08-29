import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BOARD)

class gpio:
	def __init__(self, i):
		self.i = i

	def setval(self, val):
		if val:
			GPIO.output(self.i, GPIO.HIGH)
		else:
			GPIO.output(self.i, GPIO.LOW)

	def setdir(self, dir):
		if dir == "out":
			GPIO.setup(self.i, GPIO.OUT)
		elif dir == "in":
			GPIO.setup(self.i, GPIO.IN)
		else:
			raise NameError, "invalid dir '%s'" % str(dir)

class pwm:
	def __init__(self, chan, period_us):
		GPIO.setup(chan, GPIO.OUT)
		GPIO.output(chan, GPIO.HIGH)
		self.pwm = GPIO.PWM(chan, 1000000 / period_us)
		self.pwm.start(0.5)
		self.period = period_us

	def set_dc(self, dc_us):
		self.pwm.ChangeDutyCycle(100 * dc_us / self.period)
