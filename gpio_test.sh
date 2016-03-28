#/bin/sh
# 16 7 6 5 

N=$1

if [ x$N = x ]; then
	echo error: specify gpio number
	exit 1;
fi

GPIO="/sys/class/gpio/gpio$N"

if [ ! -e $GPIO ]; then
	echo $N > /sys/class/gpio/export
fi

echo out > $GPIO/direction
echo 1 > $GPIO/value
sleep 1
echo 0 > $GPIO/value
