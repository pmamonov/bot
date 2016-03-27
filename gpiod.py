import os, sys, time, argparse, signal, ctypes, socket, threading

GPIO_PREFIX = "/sys/class/gpio"

PWM_MS = 100

pwm = {}

ipins = (16, 7, 5, 6)

timers = map(lambda i: None, range(len(ipins)))

# tcp socket to listen
soc = None

# connetion socket
conn = None

pins = []

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

def tsprint(s):
	print timestamp() + s

def do_pwm(pwm_id, l, w, p):
	while pwm[pwm_id] and time.time() < l:
		for i in p:
			pins[i].setval(1)
			time.sleep(w / 1000.)
			pins[i].setval(0)
			time.sleep((PWM_MS - w) / 1000.)

def process_cmd(c):
	ret = "ERROR"
	tsprint(c)
	t = c.split()
	if len(t) > 0:
		if t[0] == 'set':
			out, tim = map(int, t[1:])
			if type(timers[out]) is threading._Timer:
				timers[out].cancel()
				timers[out].join()
			pins[out].setval(1)
			timers[out] = threading.Timer(1e-3 * tim,
				lambda o=pins[out]: o.setval(0))
			timers[out].start()
			ret = "OK"
		elif t[0] == 'rst':
			out = int(t[1])
			pins[out].setval(0)
			ret = "OK"
		elif t[0] == 'pypwm':
			l = time.time() + int(t[1]) * 1e-3
			w = int(t[2])
			p = []
			for s in t[3:]:
				p.append(int(s))
			pwm_id = 0
			while pwm_id in pwm.keys():
				pwm_id += 1
			t = threading.Thread(target=do_pwm, args=(pwm_id, l, w, p))
			pwm[pwm_id] = t
			t.start()
			ret = "%d" % pwm_id
		elif t[0] == 'pypwmoff':
			i = int(t[1])
			t = pwm[i]
			pwm[i] = 0
			t.join()
			pwm.pop(i)
			ret = "OK"

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
