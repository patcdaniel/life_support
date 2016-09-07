#!/bin/bash
while true; do
	python /home/pi/Documents/reef_lifesupport/lifesupport.py &
	wait $!
	sleep 10
done
exit
	