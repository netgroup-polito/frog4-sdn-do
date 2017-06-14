#!/bin/sh
ifconfig h2-eth0 down
ifconfig h2-eth0 up
route add default gw 10.0.0.254
