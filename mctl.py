import os
import socket
from Tkinter import *
from tkMessageBox import showerror,showinfo
import tkFont

root = None
soc = None
repeat = 0
down = 0
keys = []

def go(e):
	global down
	down += 1
	keys.append(e.char)
	_go()

def _go():
	global repeat, root, keys

	root.after_cancel(repeat)
	c = keys[-1]
	if c in "awsd":
		soc.send(c + "\n")
		repeat = root.after(250, _go)


def stop(e):
	global down
	c = e.char
	if c in keys:
		keys.pop(keys.index(c))
	if len(keys):
		return
	root.after_cancel(repeat)
	print "stop"
	soc.send("x\n")

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
