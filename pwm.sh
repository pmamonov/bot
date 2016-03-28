#!/bin/sh

PWM_CHIP=/sys/class/pwm/pwmchip0

CHAN=$1
PERIOD=$2
DUTY=$3

PWM=$PWM_CHIP/pwm$CHAN

if [ ! -d $PWM ]; then
	echo $CHAN > $PWM_CHIP/export
fi

echo "$PERIOD"000 > $PWM/period
echo  "$DUTY"000 > $PWM/duty_cycle
echo 1 > $PWM/enable
