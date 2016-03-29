#!/bin/sh

pwm=$1
period=$2
start=$3
step=$4
stop=$5
t=$6

for i in $(seq $start $step $stop); do
	./pwm.sh $pwm $period $i
	sleep $t
done
