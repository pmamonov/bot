import os, sys, time, argparse, signal, ctypes, socket, threading

GPIO_PREFIX = "/sys/class/gpio"
PWM_PREFIX = "/sys/class/pwm/pwmchip0"

ipins = (7, 16, 5, 6)

timers = map(lambda i: None, range(len(ipins)))

# tcp socket to listen
soc = None

# connetion socket
conn = None

pins = []

mpwm = None
pwm_timestamp = time.time()
pwm_target = 0
pwm_run = True

class pwm:
	def __init__(self, chan, period_us, pref=PWM_PREFIX):
		root = pref + ("/pwm%d" % chan)
		if not os.path.isdir(root):
			export = open(pref + "/export", 'w')
			export.write("%d\n" % chan)
			export.close()
		per = open(root + "/period", 'w')
		per.write("%d\n" % (period_us * 1000))
		per.close()
		self.duty_cycle = root + "/duty_cycle"
		self.set_dc(0)
		en = open(root + "/enable", 'w')
		en.write("1\n")
		en.close()

	def set_dc(self, dc_us):
		dc = open(self.duty_cycle, 'w')
		dc.write("%d\n" % (dc_us * 1000))
		dc.close()

class gpio:
	def __init__(self, igpio, pref=GPIO_PREFIX):
		self.value = []
		self.direction = []
		root = "%s/gpio%d" % (pref, i)
		if not os.path.isdir(root):
			export = open(pref + "/export", 'w')
			export.write("%d\n" % igpio)
			export.close()
		self.value = root + "/value"
		self.direction = root + "/direction"
				
	def setval(self, val):
		f = open(self.value, 'w')
		f.write("%d\n" % val)
		f.close()

	def setdir(self, dir):
		f = open(self.direction, 'w')
		f.write("%s\n" % dir)
		f.close()

def timestamp():
	t = time.localtime()
	return "%d-%02d-%02d_%02d:%02d:%02d> " % (t.tm_year,
						  t.tm_mon,
						  t.tm_mday,
						  t.tm_hour,
						  t.tm_min,
						  t.tm_sec)
def fpwm():
	global pwm_target, pwm_timestamp, mpwm
	pwm_delay = 0.1
	pwm_step = 1
	pwm_timeout = 1
	pwm_low = 60
	dc = 0
	while pwm_run:
		if (time.time() - pwm_timestamp > pwm_timeout):
			pwm_target = 0
		if dc < pwm_target:
			if dc < pwm_low:
				dc = pwm_low
			else:
				dc += pwm_step
		if dc > pwm_target:
			if dc <= pwm_low:
				dc = pwm_target
			else:
				dc -= pwm_step
		mpwm.set_dc(dc)
		if dc != pwm_target:
			tsprint("pwm: %d -> %d" % (dc, pwm_target))
		time.sleep(pwm_delay)

def tsprint(s):
	print timestamp() + s

def process_cmd(c):
	global pwm_target, pwm_timestamp, mpwm

	ret = "OK"
	tsprint(c)
	t = c.split()
	if len(t) > 0 and t[0] in "awsdx":
		if t[0] == 'w':
			pins[0].setval(1)
			pins[1].setval(0)
			pins[2].setval(1)
			pins[3].setval(0)
		elif t[0] == 's':
			pins[0].setval(0)
			pins[1].setval(1)
			pins[2].setval(0)
			pins[3].setval(1)
		elif t[0] == 'a':
			pins[0].setval(1)
			pins[1].setval(0)
			pins[2].setval(0)
			pins[3].setval(1)
		elif t[0] == 'd':
			pins[0].setval(0)
			pins[1].setval(1)
			pins[2].setval(1)
			pins[3].setval(0)
		if t[0] == 'x':
			pins[0].setval(0)
			pins[1].setval(0)
			pins[2].setval(0)
			pins[3].setval(0)

	tsprint(ret)
	return ret

# workaround signal handling in python
libc = ctypes.cdll.LoadLibrary("libc.so.6")
mask = '\x00' * 17 # 16 byte empty mask + null terminator 
libc.sigprocmask(2, mask, None)

# parse arguments
prs = argparse.ArgumentParser(description="")
prs.add_argument('-x', dest="pidf", metavar='FILENAME', type=str, help='PID file', default='pigpiod.pid')
prs.add_argument('-d', dest="daemon",	action="store_true", help='daemonize')
prs.add_argument('-l', dest="log", metavar='FILE', type=str, help='log file')
prs.add_argument('-p', dest="port", metavar='PORT', type=int, help='port number to listen',default=6660)
prs.add_argument('-i', dest="iface", metavar='INTERFACE', type=str, help='hostname or ip adress to listen',default='0.0.0.0')
args = prs.parse_args()

# daemonize if requested
if args.daemon:
	if os.fork() > 0:
		sys.exit(0)
	os.setsid()
	if os.fork() > 0:
		sys.exit(0)
	os.umask(0)
	import resource		# Resource usage information.
	maxfd = resource.getrlimit(resource.RLIMIT_NOFILE)[1]
	if (maxfd == resource.RLIM_INFINITY):
		maxfd = 1024
	for fd in range(0, maxfd):
		try:
			os.close(fd)
		except OSError:	# ERROR, fd wasn't open to begin with (ignored)
			pass

# set SIGTERM signal handler
signal.signal(signal.SIGTERM, quit)
signal.signal(signal.SIGINT, quit)

# redirect stdout,stderr to log file
sys.stdin = open('/dev/null', 'r')
if args.log:
	sys.stdout = open(args.log, 'a', 0)
	sys.stderr = sys.stdout

# write pid to file
f = open(args.pidf, 'w')
f.write(str(os.getpid()))
f.close()

# create socket to listen
try:
	soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	soc.bind((args.iface, args.port))
except socket.error as err:
	print err
	quit(0,0)

soc.listen(1)

tsprint("Daemon started")

mpwm = pwm(2, 100)
mpwm.set_dc(65)
#tpwm = threading.Thread(target=fpwm)
#tpwm.start()

for i in ipins:
	pins.append(gpio(i))
	pins[-1].setdir("out")
	pins[-1].setval(0)

while 1:
	conn = None
	conn, addr = soc.accept()
	tsprint("Accept connection from %s" % str(addr))
	buf = ''
	while 1:
		d = conn.recv(4096)
		if not d:
			break
		buf += d
		while 1:
			stop = buf.find('\n')
			if stop >= 0:
				stop += 1
				cmd = buf[:stop]
				buf = buf[stop:]
				conn.send(process_cmd(cmd.strip()) + '\n')
			else:
				break

	tsprint("Connection closed")
