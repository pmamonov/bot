import os
import socket
from Tkinter import *
from tkMessageBox import showerror,showinfo
import tkFont

root = None
soc = None
repeat = 0

def go(e):
	global repeat, root

	c = e.char
	root.after_cancel(repeat)
	print c,
	if c == 'w':
		soc.send("set 0 1000\nset 2 1000\n")
	elif c == 's':
		soc.send("set 1 1000\nset 3 1000\n")
	elif c == 'a':
		soc.send("set 0 1000\nset 3 1000\n")
	elif c == 'd':
		soc.send("set 1 1000\nset 2 1000\n")

	repeat = root.after(500, go, e)


def stop(e):
	root.after_cancel(repeat)
	print "stop"
	for i in xrange(4):
		soc.send("rst %d\n" % i)

soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
soc.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
soc.connect((sys.argv[1], int(sys.argv[2])))


root = Tk()
root.title("mctl")
root.resizable(0,0)

#fnt = tkFont.Font(font=("Helvetica",14,NORMAL))
#root.option_add("*Font", fnt)

frame = Frame(root, width=200, height=200)
frame.bind("q", lambda r=root: root.quit())
frame.bind("<KeyPress>", go)
frame.bind("<KeyRelease>", stop)
frame.pack()
frame.focus_set()

os.system("xset r off")

root.mainloop()

os.system("xset r on")

soc.close()
